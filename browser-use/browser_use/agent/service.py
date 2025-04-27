from __future__ import annotations

import asyncio
import gc
import inspect
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, TypeVar, Union

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
	BaseMessage,
	HumanMessage,
	SystemMessage,
)

# from lmnr.sdk.decorators import observe
from pydantic import BaseModel, ValidationError
from loguru import logger as loguru_logger
import pandas as pd
import uuid

# Custom dummy AgentStart class to fix import error
class AgentStart:
	"""Placeholder for the missing AgentStart class"""
	pass

from browser_use.agent.gif import create_history_gif
from browser_use.agent.memory.service import Memory, MemorySettings
from browser_use.agent.message_manager.service import MessageManager, MessageManagerSettings
from browser_use.agent.message_manager.utils import convert_input_messages, extract_json_from_model_output, save_conversation
from browser_use.agent.prompts import AgentMessagePrompt, PlannerPrompt, SystemPrompt
# from browser_use.agent.types import AgentStart  # Commented out since we're defining it above
from browser_use.agent.views import (
	REQUIRED_LLM_API_ENV_VARS,
	ActionResult,
	AgentError,
	AgentHistory,
	AgentHistoryList,
	AgentOutput,
	AgentSettings,
	AgentState,
	AgentStepInfo,
	StepMetadata,
	ToolCallingMethod,
)
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from browser_use.browser.views import BrowserState, BrowserStateHistory
from browser_use.controller.registry.views import ActionModel
from browser_use.controller.service import Controller
from browser_use.dom.history_tree_processor.service import (
	DOMHistoryElement,
	HistoryTreeProcessor,
)
from browser_use.exceptions import LLMException
from browser_use.telemetry.service import ProductTelemetry
from browser_use.telemetry.views import (
	AgentEndTelemetryEvent,
	AgentRunTelemetryEvent,
	AgentStepTelemetryEvent,
)
from browser_use.utils import check_env_variables, time_execution_async, time_execution_sync

load_dotenv()

# Set up logging format
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO
)

# Create a unique directory for each run using a timestamp and UUID
run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()}"
run_directory = os.path.join('organized', 'runs', run_id)

# Create directories for logs, results, Excel files, and screenshots within the run directory
log_directory = os.path.join(run_directory, 'logs')
results_directory = os.path.join(run_directory, 'results')
excel_directory = os.path.join(run_directory, 'excel')
screenshots_directory = os.path.join(run_directory, 'screenshots')

# Create directories if they don't exist
os.makedirs(log_directory, exist_ok=True)
os.makedirs(results_directory, exist_ok=True)
os.makedirs(excel_directory, exist_ok=True)
os.makedirs(screenshots_directory, exist_ok=True)

# Set up loguru for structured logging
loguru_logger.add(os.path.join(log_directory, 'agent.log'), format="{time} {level} {message}", level="INFO")

SKIP_LLM_API_KEY_VERIFICATION = os.environ.get('SKIP_LLM_API_KEY_VERIFICATION', 'false').lower()[0] in 'ty1'

def log_response(response: AgentOutput) -> None:
	"""Utility function to log the model's response."""

	if 'Success' in response.current_state.evaluation_previous_goal:
		emoji = '👍'
	elif 'Failed' in response.current_state.evaluation_previous_goal:
		emoji = '⚠'
	else:
		emoji = '🤷'

	loguru_logger.info(f'{emoji} Eval: {response.current_state.evaluation_previous_goal}')
	loguru_logger.info(f'🧠 Memory: {response.current_state.memory}')
	loguru_logger.info(f'🎯 Next goal: {response.current_state.next_goal}')
	for i, action in enumerate(response.action):
		loguru_logger.info(f'🛠️  Action {i + 1}/{len(response.action)}: {action.model_dump_json(exclude_unset=True)}')


Context = TypeVar('Context')

AgentHookFunc = Callable[['Agent'], Awaitable[None]]


class Agent(Generic[Context]):
	@time_execution_sync('--init (agent)')
	def __init__(
		self,
		task: str,
		llm: BaseChatModel,
		# Optional parameters
		browser: Browser | None = None,
		browser_context: BrowserContext | None = None,
		controller: Controller[Context] = Controller(),
		# Initial agent run parameters
		sensitive_data: Optional[Dict[str, str]] = None,
		initial_actions: Optional[List[Dict[str, Dict[str, Any]]]] = None,
		# Cloud Callbacks
		register_new_step_callback: Union[
			Callable[['BrowserState', 'AgentOutput', int], None],  # Sync callback
			Callable[['BrowserState', 'AgentOutput', int], Awaitable[None]],  # Async callback
			None,
		] = None,
		register_done_callback: Union[
			Callable[['AgentHistoryList'], Awaitable[None]],  # Async Callback
			Callable[['AgentHistoryList'], None],  # Sync Callback
			None,
		] = None,
		register_external_agent_status_raise_error_callback: Callable[[], Awaitable[bool]] | None = None,
		# Agent settings
		use_vision: bool = True,
		use_vision_for_planner: bool = True,
		save_conversation_path: Optional[str] = None,
		save_conversation_path_encoding: Optional[str] = 'utf-8',
		max_failures: int = 3,
		retry_delay: int = 10,
		override_system_message: Optional[str] = None,
		extend_system_message: Optional[str] = None,
		max_input_tokens: int = 128000,
		validate_output: bool = True,
		message_context: Optional[str] = None,
		generate_gif: bool | str = True,
		available_file_paths: Optional[list[str]] = None,
		include_attributes: list[str] = [
			'title',
			'type',
			'name',
			'role',
			'aria-label',
			'placeholder',
			'value',
			'alt',
			'aria-expanded',
			'data-date-format',
		],
		max_actions_per_step: int = 10,
		tool_calling_method: Optional[ToolCallingMethod] = 'auto',
		page_extraction_llm: Optional[BaseChatModel] = None,
		planner_llm: Optional[BaseChatModel] = None,
		planner_interval: int = 1,  # Run planner every N steps
		is_planner_reasoning: bool = True,
		# Inject state
		injected_agent_state: Optional[AgentState] = None,
		#
		context: Context | None = None,
		# Memory settings
		enable_memory: bool = True,
		memory_interval: int = 1,
		memory_config: Optional[dict] = None,
		# Logging settings
		log_directory: str = "logs",
		results_directory: str = "results",
		excel_directory: str = "excel",
		screenshots_directory: str = "screenshots",
		gherkin_directory: str = "gherkin",
		playwright_directory: str = "playwright",
		selenium_directory: str = "selenium",
		webdriverio_directory: str = "webdriverio",
	):
		if page_extraction_llm is None:
			page_extraction_llm = llm

		# Core components
		self.task = task
		self.llm = llm
		self.controller = controller
		self.sensitive_data = sensitive_data

		self.settings = AgentSettings(
			use_vision=use_vision,
			use_vision_for_planner=use_vision_for_planner,
			save_conversation_path=save_conversation_path,
			save_conversation_path_encoding=save_conversation_path_encoding,
			max_failures=max_failures,
			retry_delay=retry_delay,
			override_system_message=override_system_message,
			extend_system_message=extend_system_message,
			max_input_tokens=max_input_tokens,
			validate_output=validate_output,
			message_context=message_context,
			generate_gif=generate_gif,
			available_file_paths=available_file_paths,
			include_attributes=include_attributes,
			max_actions_per_step=max_actions_per_step,
			tool_calling_method=tool_calling_method,
			page_extraction_llm=page_extraction_llm,
			planner_llm=planner_llm,
			planner_interval=planner_interval,
			is_planner_reasoning=is_planner_reasoning,
			enable_memory=enable_memory,
			memory_interval=memory_interval,
			memory_config=memory_config,
		)

		# Initialize state
		self.state = injected_agent_state or AgentState()

		# Action setup
		self._setup_action_models()
		self._set_browser_use_version_and_source()
		self.initial_actions = self._convert_initial_actions(initial_actions) if initial_actions else None

		# Model setup
		self._set_model_names()
		self.tool_calling_method = self._set_tool_calling_method()

		# Handle users trying to use use_vision=True with DeepSeek models
		if 'deepseek' in self.model_name.lower():
			loguru_logger.warning('⚠️ DeepSeek models do not support use_vision=True yet. Setting use_vision=False for now...')
			self.settings.use_vision = False
		if 'deepseek' in (self.planner_model_name or '').lower():
			loguru_logger.warning(
				'⚠️ DeepSeek models do not support use_vision=True yet. Setting use_vision_for_planner=False for now...'
			)
			self.settings.use_vision_for_planner = False

		loguru_logger.info(
			f'🚀 Starting task: {self.task} with model: {self.model_name}'
			f'{" +tools" if self.tool_calling_method == "function_calling" else ""}'
			f'{" +rawtools" if self.tool_calling_method == "raw" else ""}'
			f'{" +vision" if self.settings.use_vision else ""}'
			f'{" +memory" if self.settings.enable_memory else ""}, '
			f'planner_model={self.planner_model_name}'
			f'{" +reasoning" if self.settings.is_planner_reasoning else ""}'
			f'{" +vision" if self.settings.use_vision_for_planner else ""}, '
			f'extraction_model={getattr(self.settings.page_extraction_llm, "model_name", None)} '
		)

		# Start non-blocking LLM connection verification using create_task, checked later in step()
		# This will run in parallel with browser launch without leaving dangling coroutines on unclean exits
		self.llm._verified_api_keys = False
		self._verification_task = asyncio.create_task(self._verify_llm_connection())
		self._verification_task.add_done_callback(lambda _: None)

		# Initialize available actions for system prompt (only non-filtered actions)
		# These will be used for the system prompt to maintain caching
		self.unfiltered_actions = self.controller.registry.get_prompt_description()

		self.settings.message_context = self._set_message_context()

		# Initialize message manager with state
		# Initial system prompt with all actions - will be updated during each step
		self._message_manager = MessageManager(
			task=task,
			system_message=SystemPrompt(
				action_description=self.unfiltered_actions,
				max_actions_per_step=self.settings.max_actions_per_step,
				override_system_message=override_system_message,
				extend_system_message=extend_system_message,
			).get_system_message(),
			settings=MessageManagerSettings(
				max_input_tokens=self.settings.max_input_tokens,
				include_attributes=self.settings.include_attributes,
				message_context=self.settings.message_context,
				sensitive_data=sensitive_data,
				available_file_paths=self.settings.available_file_paths,
			),
			state=self.state.message_manager_state,
		)

		if self.settings.enable_memory:
			memory_settings = MemorySettings(
				agent_id=self.state.agent_id,
				interval=self.settings.memory_interval,
				config=self.settings.memory_config,
			)

			# Initialize memory
			self.memory = Memory(
				message_manager=self._message_manager,
				llm=self.llm,
				settings=memory_settings,
			)
		else:
			self.memory = None

		# Browser setup
		self.injected_browser = browser is not None
		self.injected_browser_context = browser_context is not None
		self.browser = browser or Browser()
		self.browser_context = browser_context or BrowserContext(
			browser=self.browser, config=self.browser.config.new_context_config
		)

		# Callbacks
		self.register_new_step_callback = register_new_step_callback
		self.register_done_callback = register_done_callback
		self.register_external_agent_status_raise_error_callback = register_external_agent_status_raise_error_callback

		# Context
		self.context = context

		# Telemetry
		self.telemetry = ProductTelemetry()

		if self.settings.save_conversation_path:
			loguru_logger.info(f'Saving conversation to {self.settings.save_conversation_path}')

		# Create a unique directory for each run if not provided
		run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()}"
		run_directory = os.path.join('organized', 'runs', run_id)

		# Define directories for logs, results, Excel files, and screenshots
		self.log_directory = os.path.join(run_directory, log_directory) if log_directory else os.path.join(run_directory, 'logs')
		self.results_directory = os.path.join(run_directory, results_directory) if results_directory else os.path.join(run_directory, 'results')
		self.excel_directory = os.path.join(run_directory, excel_directory) if excel_directory else os.path.join(run_directory, 'excel')
		self.screenshots_directory = os.path.join(run_directory, screenshots_directory) if screenshots_directory else os.path.join(run_directory, 'screenshots')
		self.gherkin_directory = os.path.join(run_directory, gherkin_directory) if gherkin_directory else os.path.join(run_directory, 'gherkin')
		self.playwright_directory = os.path.join(run_directory, playwright_directory) if playwright_directory else os.path.join(run_directory, 'playwright')
		self.selenium_directory = os.path.join(run_directory, selenium_directory) if selenium_directory else os.path.join(run_directory, 'selenium')
		self.webdriverio_directory = os.path.join(run_directory, webdriverio_directory) if webdriverio_directory else os.path.join(run_directory, 'webdriverio')

		# Create directories if they don't exist
		os.makedirs(self.log_directory, exist_ok=True)
		os.makedirs(self.results_directory, exist_ok=True)
		os.makedirs(self.excel_directory, exist_ok=True)
		os.makedirs(self.screenshots_directory, exist_ok=True)
		os.makedirs(self.gherkin_directory, exist_ok=True)
		os.makedirs(self.playwright_directory, exist_ok=True)
		os.makedirs(self.selenium_directory, exist_ok=True)
		os.makedirs(self.webdriverio_directory, exist_ok=True)

		# Add callback hooks for real-time progress tracking
		self.on_step_start = None  # type: Optional[Callable[[int, str], None]]
		self.on_step_complete = None  # type: Optional[Callable[[int, bool, str], None]]

	def _set_message_context(self) -> str | None:
		if self.tool_calling_method == 'raw':
			# For raw tool calling, only include actions with no filters initially
			if self.settings.message_context:
				self.settings.message_context += f'\n\nAvailable actions: {self.unfiltered_actions}'
			else:
				self.settings.message_context = f'Available actions: {self.unfiltered_actions}'
		return self.settings.message_context

	def _set_browser_use_version_and_source(self) -> None:
		"""Get the version and source of the browser-use package (git or pip in a nutshell)"""
		try:
			# First check for repository-specific files
			repo_files = ['.git', 'README.md', 'docs', 'examples']
			package_root = Path(__file__).parent.parent.parent

			# If all of these files/dirs exist, it's likely from git
			if all(Path(package_root / file).exists() for file in repo_files):
				try:
					import subprocess

					version = subprocess.check_output(['git', 'describe', '--tags']).decode('utf-8').strip()
				except Exception:
					version = 'unknown'
				source = 'git'
			else:
				# If no repo files found, try getting version from pip
				import pkg_resources

				version = pkg_resources.get_distribution('browser-use').version
				source = 'pip'
		except Exception:
			version = 'unknown'
			source = 'unknown'

		loguru_logger.debug(f'Version: {version}, Source: {source}')
		self.version = version
		self.source = source

	def _set_model_names(self) -> None:
		self.chat_model_library = self.llm.__class__.__name__
		self.model_name = 'Unknown'
		if hasattr(self.llm, 'model_name'):
			model = self.llm.model_name  # type: ignore
			self.model_name = model if model is not None else 'Unknown'
		elif hasattr(self.llm, 'model'):
			model = self.llm.model  # type: ignore
			self.model_name = model if model is not None else 'Unknown'

		if self.settings.planner_llm:
			if hasattr(self.settings.planner_llm, 'model_name'):
				self.planner_model_name = self.settings.planner_llm.model_name  # type: ignore
			elif hasattr(self.settings.planner_llm, 'model'):
				self.planner_model_name = self.settings.planner_llm.model  # type: ignore
			else:
				self.planner_model_name = 'Unknown'
		else:
			self.planner_model_name = None

	def _setup_action_models(self) -> None:
		"""Setup dynamic action models from controller's registry"""
		# Initially only include actions with no filters
		self.ActionModel = self.controller.registry.create_action_model()
		# Create output model with the dynamic actions
		self.AgentOutput = AgentOutput.type_with_custom_actions(self.ActionModel)

		# used to force the done action when max_steps is reached
		self.DoneActionModel = self.controller.registry.create_action_model(include_actions=['done'])
		self.DoneAgentOutput = AgentOutput.type_with_custom_actions(self.DoneActionModel)

	def _set_tool_calling_method(self) -> Optional[ToolCallingMethod]:
		tool_calling_method = self.settings.tool_calling_method
		if tool_calling_method == 'auto':
			if 'deepseek-reasoner' in self.model_name or 'deepseek-r1' in self.model_name:
				return 'raw'
			elif self.chat_model_library == 'ChatGoogleGenerativeAI':
				return None
			elif self.chat_model_library == 'ChatOpenAI':
				return 'function_calling'
			elif self.chat_model_library == 'AzureChatOpenAI':
				return 'function_calling'
			else:
				return None
		else:
			return tool_calling_method

	def add_new_task(self, new_task: str) -> None:
		self._message_manager.add_new_task(new_task)

	async def _raise_if_stopped_or_paused(self) -> None:
		"""Utility function that raises an InterruptedError if the agent is stopped or paused."""

		if self.register_external_agent_status_raise_error_callback:
			if await self.register_external_agent_status_raise_error_callback():
				raise InterruptedError

		if self.state.stopped or self.state.paused:
			# logger.debug('Agent paused after getting state')
			raise InterruptedError

	# @observe(name='agent.step', ignore_output=True, ignore_input=True)
	@time_execution_async('--step (agent)')
	async def step(self, step_info: Optional[AgentStepInfo] = None, max_steps: int = 100) -> None:
		"""Execute one step of the task"""
		loguru_logger.info(f'📍 Step {self.state.n_steps}/{max_steps} - Task: {self.task}')
		state = None
		model_output = None
		result: list[ActionResult] = []
		step_start_time = time.time()
		tokens = 0

		try:
			# Notify step start if callback is set
			if self.on_step_start and callable(self.on_step_start):
				step_description = f"Step {self.state.n_steps + 1}/{max_steps}"
				self.on_step_start(self.state.n_steps + 1, step_description)
				
			state = await self.browser_context.get_state(cache_clickable_elements_hashes=True)
			active_page = await self.browser_context.get_current_page()

			# generate procedural memory if needed
			if self.settings.enable_memory and self.memory and self.state.n_steps % self.settings.memory_interval == 0:
				self.memory.create_procedural_memory(self.state.n_steps)

			await self._raise_if_stopped_or_paused()

			# Update action models with page-specific actions
			await self._update_action_models_for_page(active_page)

			# Get page-specific filtered actions
			page_filtered_actions = self.controller.registry.get_prompt_description(active_page)

			# If there are page-specific actions, add them as a special message for this step only
			if page_filtered_actions:
				page_action_message = f'For this page, these additional actions are available:\n{page_filtered_actions}'
				self._message_manager._add_message_with_tokens(HumanMessage(content=page_action_message))

			# If using raw tool calling method, we need to update the message context with new actions
			if self.tool_calling_method == 'raw':
				# For raw tool calling, get all non-filtered actions plus the page-filtered ones
				all_unfiltered_actions = self.controller.registry.get_prompt_description()
				all_actions = all_unfiltered_actions
				if page_filtered_actions:
					all_actions += '\n' + page_filtered_actions

				context_lines = (self._message_manager.settings.message_context or '').split('\n')
				non_action_lines = [line for line in context_lines if not line.startswith('Available actions:')]
				updated_context = '\n'.join(non_action_lines)
				if updated_context:
					updated_context += f'\n\nAvailable actions: {all_actions}'
				else:
					updated_context = f'Available actions: {all_actions}'
				self._message_manager.settings.message_context = updated_context

			self._message_manager.add_state_message(state, self.state.last_result, step_info, self.settings.use_vision)

			# Run planner at specified intervals if planner is configured
			if self.settings.planner_llm and self.state.n_steps % self.settings.planner_interval == 0:
				plan = await self._run_planner()
				# add plan before last state message
				self._message_manager.add_plan(plan, position=-1)

			if step_info and step_info.is_last_step():
				# Add last step warning if needed
				msg = 'Now comes your last step. Use only the "done" action now. No other actions - so here your action sequence must have length 1.'
				msg += '\nIf the task is not yet fully finished as requested by the user, set success in "done" to false! E.g. if not all steps are fully completed.'
				msg += '\nIf the task is fully finished, set success in "done" to true.'
				msg += '\nInclude everything you found out for the ultimate task in the done text.'
				loguru_logger.info('Last step finishing up')
				self._message_manager._add_message_with_tokens(HumanMessage(content=msg))
				self.AgentOutput = self.DoneAgentOutput

			input_messages = self._message_manager.get_messages()
			tokens = self._message_manager.state.history.current_tokens

			try:
				model_output = await self.get_next_action(input_messages)

				# Check again for paused/stopped state after getting model output
				# This is needed in case Ctrl+C was pressed during the get_next_action call
				await self._raise_if_stopped_or_paused()

				self.state.n_steps += 1

				if self.register_new_step_callback:
					if inspect.iscoroutinefunction(self.register_new_step_callback):
						await self.register_new_step_callback(state, model_output, self.state.n_steps)
					else:
						self.register_new_step_callback(state, model_output, self.state.n_steps)
				if self.settings.save_conversation_path:
					target = self.settings.save_conversation_path + f'_{self.state.n_steps}.txt'
					save_conversation(input_messages, model_output, target, self.settings.save_conversation_path_encoding)

				self._message_manager._remove_last_state_message()  # we dont want the whole state in the chat history

				# check again if Ctrl+C was pressed before we commit the output to history
				await self._raise_if_stopped_or_paused()

				self._message_manager.add_model_output(model_output)
			except asyncio.CancelledError:
				# Task was cancelled due to Ctrl+C
				self._message_manager._remove_last_state_message()
				raise InterruptedError('Model query cancelled by user')
			except InterruptedError:
				# Agent was paused during get_next_action
				self._message_manager._remove_last_state_message()
				raise  # Re-raise to be caught by the outer try/except
			except Exception as e:
				# model call failed, remove last state message from history
				self._message_manager._remove_last_state_message()
				raise e

			result: list[ActionResult] = await self.multi_act(model_output.action)

			self.state.last_result = result

			if len(result) > 0 and result[-1].is_done:
				loguru_logger.info(f'📄 Result: {result[-1].extracted_content}')

			self.state.consecutive_failures = 0

			# Notify step completion if callback is set
			if self.on_step_complete and callable(self.on_step_complete):
				success = all(r.success for r in result) if result else False
				details = "\n".join([r.extracted_content for r in result if r.extracted_content])
				self.on_step_complete(self.state.n_steps, success, details)

		except InterruptedError:
			# logger.debug('Agent paused')
			self.state.last_result = [
				ActionResult(
					error='The agent was paused mid-step - the last action might need to be repeated', include_in_memory=False
				)
			]
			return
		except asyncio.CancelledError:
			# Directly handle the case where the step is cancelled at a higher level
			# logger.debug('Task cancelled - agent was paused with Ctrl+C')
			self.state.last_result = [ActionResult(error='The agent was paused with Ctrl+C', include_in_memory=False)]
			raise InterruptedError('Step cancelled by user')
		except Exception as e:
			result = await self._handle_step_error(e)
			self.state.last_result = result
			# Notify step failure if callback is set
			if self.on_step_complete and callable(self.on_step_complete):
				self.on_step_complete(self.state.n_steps, False, f"Error: {str(e)}")

		finally:
			step_end_time = time.time()
			actions = [a.model_dump(exclude_unset=True) for a in model_output.action] if model_output else []
			self.telemetry.capture(
				AgentStepTelemetryEvent(
					agent_id=self.state.agent_id,
					step=self.state.n_steps,
					actions=actions,
					consecutive_failures=self.state.consecutive_failures,
					step_error=[r.error for r in result if r.error] if result else ['No result'],
				)
			)
			if state:
				metadata = StepMetadata(
					step_number=self.state.n_steps,
					step_start_time=step_start_time,
					step_end_time=step_end_time,
					input_tokens=tokens,
				)
				self._make_history_item(model_output, state, result, metadata)
				self._save_log_and_screenshot(self.state.n_steps, state, result)

	def _save_log_and_screenshot(self, step_number: int, state: BrowserState, result: list[ActionResult]):
		"""Save logs and screenshots for the current step."""
		timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
		log_file = os.path.join(self.log_directory, f"step_{step_number}_{timestamp}.log")
		screenshot_file = os.path.join(self.screenshots_directory, f"step_{step_number}_{timestamp}.png")

		# Save log
		with open(log_file, "w", encoding="utf-8") as log:
			log.write(f"Step {step_number}\n")
			log.write(f"URL: {state.url}\n")
			log.write(f"Title: {state.title}\n")
			log.write(f"Actions: {len(result)}\n")
			for i, action_result in enumerate(result):
				log.write(f"Action {i + 1}: {action_result.model_dump_json(exclude_unset=True)}\n")

		# Save screenshot
		if state.screenshot:
			# Convert screenshot to bytes if it's a string
			screenshot_data = state.screenshot.encode('utf-8') if isinstance(state.screenshot, str) else state.screenshot
			with open(screenshot_file, "wb") as screenshot:
				screenshot.write(screenshot_data)

	@time_execution_async('--handle_step_error (agent)')
	async def _handle_step_error(self, error: Exception) -> list[ActionResult]:
		"""Handle all types of errors that can occur during a step"""
		include_trace = loguru_logger.level("DEBUG")
		error_msg = AgentError.format_error(error, include_trace=include_trace)
		prefix = f'❌ Result failed {self.state.consecutive_failures + 1}/{self.settings.max_failures} times:\n '
		self.state.consecutive_failures += 1

		if 'Browser closed' in error_msg:
			loguru_logger.error('❌  Browser is closed or disconnected, unable to proceed')
			return [ActionResult(error='Browser closed or disconnected, unable to proceed', include_in_memory=False)]

		if isinstance(error, (ValidationError, ValueError)):
			loguru_logger.error(f'{prefix}{error_msg}')
			if 'Max token limit reached' in error_msg:
				# cut tokens from history
				self._message_manager.settings.max_input_tokens = self.settings.max_input_tokens - 500
				loguru_logger.info(
					f'Cutting tokens from history - new max input tokens: {self._message_manager.settings.max_input_tokens}'
				)
				self._message_manager.cut_messages()
			elif 'Could not parse response' in error_msg:
				# give model a hint how output should look like
				error_msg += '\n\nReturn a valid JSON object with the required fields.'

		else:
			from anthropic import RateLimitError as AnthropicRateLimitError
			from google.api_core.exceptions import ResourceExhausted
			from openai import RateLimitError

			# Define a tuple of rate limit error types for easier maintenance
			RATE_LIMIT_ERRORS = (
				RateLimitError,  # OpenAI
				ResourceExhausted,  # Google
				AnthropicRateLimitError,  # Anthropic
			)

			if isinstance(error, RATE_LIMIT_ERRORS):
				loguru_logger.warning(f'{prefix}{error_msg}')
				await asyncio.sleep(self.settings.retry_delay)
			else:
				loguru_logger.error(f'{prefix}{error_msg}')

		return [ActionResult(error=error_msg, include_in_memory=True)]

	def _make_history_item(
		self,
		model_output: AgentOutput | None,
		state: BrowserState,
		result: list[ActionResult],
		metadata: Optional[StepMetadata] = None,
	) -> None:
		"""Create and store history item"""

		if model_output:
			interacted_elements = AgentHistory.get_interacted_element(model_output, state.selector_map)
		else:
			interacted_elements = [None]

		state_history = BrowserStateHistory(
			url=state.url,
			title=state.title,
			tabs=state.tabs,
			interacted_element=interacted_elements,
			screenshot=state.screenshot,
		)

		history_item = AgentHistory(model_output=model_output, result=result, state=state_history, metadata=metadata)

		self.state.history.history.append(history_item)

	THINK_TAGS = re.compile(r'<think>.*?</think>', re.DOTALL)
	STRAY_CLOSE_TAG = re.compile(r'.*?</think>', re.DOTALL)

	def _remove_think_tags(self, text: str) -> str:
		# Step 1: Remove well-formed <think>...</think>
		text = re.sub(self.THINK_TAGS, '', text)
		# Step 2: If there's an unmatched closing tag </think>,
		#         remove everything up to and including that.
		text = re.sub(self.STRAY_CLOSE_TAG, '', text)
		return text.strip()

	def _convert_input_messages(self, input_messages: list[BaseMessage]) -> list[BaseMessage]:
		"""Convert input messages to the correct format"""
		if self.model_name == 'deepseek-reasoner' or 'deepseek-r1' in self.model_name:
			return convert_input_messages(input_messages, self.model_name)
		else:
			return input_messages

	@time_execution_async('--get_next_action (agent)')
	async def get_next_action(self, input_messages: list[BaseMessage]) -> AgentOutput:
		"""Get next action from LLM based on current state"""
		input_messages = self._convert_input_messages(input_messages)

		if self.tool_calling_method == 'raw':
			loguru_logger.debug(f'Using {self.tool_calling_method} for {self.chat_model_library}')
			try:
				output = self.llm.invoke(input_messages)
				response = {'raw': output, 'parsed': None}
			except Exception as e:
				loguru_logger.error(f'Failed to invoke model: {str(e)}')
				raise LLMException(401, 'LLM API call failed') from e
			# TODO: currently invoke does not return reasoning_content, we should override invoke
			output.content = self._remove_think_tags(str(output.content))
			try:
				parsed_json = extract_json_from_model_output(output.content)
				parsed = self.AgentOutput(**parsed_json)
				response['parsed'] = parsed
			except (ValueError, ValidationError) as e:
				loguru_logger.warning(f'Failed to parse model output: {output} {str(e)}')
				raise ValueError('Could not parse response.')

		elif self.tool_calling_method is None:
			structured_llm = self.llm.with_structured_output(self.AgentOutput, include_raw=True)
			try:
				response: dict[str, Any] = await structured_llm.ainvoke(input_messages)  # type: ignore
				parsed: AgentOutput | None = response['parsed']

			except Exception as e:
				loguru_logger.error(f'Failed to invoke model: {str(e)}')
				raise LLMException(401, 'LLM API call failed') from e

		else:
			loguru_logger.debug(f'Using {self.tool_calling_method} for {self.chat_model_library}')
			structured_llm = self.llm.with_structured_output(self.AgentOutput, include_raw=True, method=self.tool_calling_method)
			response: dict[str, Any] = await structured_llm.ainvoke(input_messages)  # type: ignore

		# Handle tool call responses
		if response.get('parsing_error') and 'raw' in response:
			raw_msg = response['raw']
			if hasattr(raw_msg, 'tool_calls') and raw_msg.tool_calls:
				# Convert tool calls to AgentOutput format

				tool_call = raw_msg.tool_calls[0]  # Take first tool call

				# Create current state
				tool_call_name = tool_call['name']
				tool_call_args = tool_call['args']

				current_state = {
					'page_summary': 'Processing tool call',
					'evaluation_previous_goal': 'Executing action',
					'memory': 'Using tool call',
					'next_goal': f'Execute {tool_call_name}',
				}

				# Create action from tool call
				action = {tool_call_name: tool_call_args}

				parsed = self.AgentOutput(current_state=current_state, action=[self.ActionModel(**action)])
			else:
				parsed = None
		else:
			parsed = response['parsed']

		if not parsed:
			try:
				parsed_json = extract_json_from_model_output(response['raw'].content)
				parsed = self.AgentOutput(**parsed_json)
			except Exception as e:
				loguru_logger.warning(f'Failed to parse model output: {response["raw"].content} {str(e)}')
				raise ValueError('Could not parse response.')

		# cut the number of actions to max_actions_per_step if needed
		if len(parsed.action) > self.settings.max_actions_per_step:
			parsed.action = parsed.action[: self.settings.max_actions_per_step]

		if not (hasattr(self.state, 'paused') and (self.state.paused or self.state.stopped)):
			log_response(parsed)

		return parsed

	def _log_agent_run(self) -> None:
		"""Log the agent run"""
		loguru_logger.info(f'🚀 Starting task: {self.task} with model: {self.model_name}')

		loguru_logger.debug(f'Version: {self.version}, Source: {self.source}')
		self.telemetry.capture(
			AgentRunTelemetryEvent(
				agent_id=self.state.agent_id,
				use_vision=self.settings.use_vision,
				task=self.task,
				model_name=self.model_name,
				chat_model_library=self.chat_model_library,
				version=self.version,
				source=self.source,
			)
		)

	async def take_step(self) -> tuple[bool, bool]:
		"""Take a step

		Returns:
			Tuple[bool, bool]: (is_done, is_valid)
		"""
		await self.step()

		if self.state.history.is_done():
			if self.settings.validate_output:
				if not await self._validate_output():
					return True, False

			await self.log_completion()
			if self.register_done_callback:
				if inspect.iscoroutinefunction(self.register_done_callback):
					await self.register_done_callback(self.state.history)
				else:
					self.register_done_callback(self.state.history)
			return True, True

		return False, False

	# @observe(name='agent.run', ignore_output=True)
	@time_execution_async('--run (agent)')
	async def run(
		self, max_steps: int = 100, on_step_start: AgentHookFunc | None = None, on_step_end: AgentHookFunc | None = None
	) -> AgentHistoryList:
		"""Execute the task with maximum number of steps"""

		loop = asyncio.get_event_loop()

		# Set up the Ctrl+C signal handler with callbacks specific to this agent
		from browser_use.utils import SignalHandler

		signal_handler = SignalHandler(
			loop=loop,
			pause_callback=self.pause,
			resume_callback=self.resume,
			custom_exit_callback=None,  # No special cleanup needed on forced exit
			exit_on_second_int=True,
		)
		signal_handler.register()

		# Wait for verification task to complete if it exists
		if hasattr(self, '_verification_task') and not self._verification_task.done():
			try:
				await self._verification_task
			except Exception:
				# Error already logged in the task
				pass

		# Check that verification was successful
		assert self.llm._verified_api_keys or SKIP_LLM_API_KEY_VERIFICATION, (
			'Failed to connect to LLM API or LLM API is not responding correctly'
		)

		try:
			self._log_agent_run()

			# Execute initial actions if provided
			if self.initial_actions:
				result = await self.multi_act(self.initial_actions, check_for_new_elements=False)
				self.state.last_result = result

			for step in range(max_steps):
				# Check if waiting for user input after Ctrl+C
				if self.state.paused:
					signal_handler.wait_for_resume()
					signal_handler.reset()

				# Check if we should stop due to too many failures
				if self.state.consecutive_failures >= self.settings.max_failures:
					loguru_logger.error(f'❌ Stopping due to {self.settings.max_failures} consecutive failures')
					break

				# Check control flags before each step
				if self.state.stopped:
					loguru_logger.info('Agent stopped')
					break

				while self.state.paused:
					await asyncio.sleep(0.2)  # Small delay to prevent CPU spinning
					if self.state.stopped:  # Allow stopping while paused
						break

				if on_step_start is not None:
					await on_step_start(self)

				step_info = AgentStepInfo(step_number=step, max_steps=max_steps)
				await self.step(step_info)

				if on_step_end is not None:
					await on_step_end(self)

				if self.state.history.is_done():
					if self.settings.validate_output and step < max_steps - 1:
						if not await self._validate_output():
							continue

					await self.log_completion()
					break
			else:
				loguru_logger.info('❌ Failed to complete task in maximum steps')

			return self.state.history

		except KeyboardInterrupt:
			# Already handled by our signal handler, but catch any direct KeyboardInterrupt as well
			loguru_logger.info('Got KeyboardInterrupt during execution, returning current history')
			return self.state.history

		finally:
			# Unregister signal handlers before cleanup
			signal_handler.unregister()

			self.telemetry.capture(
				AgentEndTelemetryEvent(
					agent_id=self.state.agent_id,
					is_done=self.state.history.is_done(),
					success=self.state.history.is_successful(),
					steps=self.state.n_steps,
					max_steps_reached=self.state.n_steps >= max_steps,
					errors=self.state.history.errors(),
					total_input_tokens=self.state.history.total_input_tokens(),
					total_duration_seconds=self.state.history.total_duration_seconds(),
				)
			)

			await self.close()

			if self.settings.generate_gif:
				output_path: str = 'agent_history.gif'
				if isinstance(self.settings.generate_gif, str):
					output_path = self.settings.generate_gif

				create_history_gif(task=self.task, history=self.state.history, output_path=output_path)

			# Generate all code artifacts at the end of the run
			try:
				# Ensure all required directories exist
				if not hasattr(self, 'results_directory') or self.results_directory is None:
					run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()}"
					self.results_directory = os.path.join('organized', 'runs', run_id, 'results')
					os.makedirs(self.results_directory, exist_ok=True)
					loguru_logger.warning(f"Results directory missing, created: {self.results_directory}")

				# Create all necessary subdirectories with fallbacks
				self.excel_directory = os.path.join(self.results_directory, 'excel') if not hasattr(self, 'excel_directory') or self.excel_directory is None else self.excel_directory
				self.gherkin_directory = os.path.join(self.results_directory, 'gherkin') if not hasattr(self, 'gherkin_directory') or self.gherkin_directory is None else self.gherkin_directory
				self.playwright_directory = os.path.join(self.results_directory, 'playwright') if not hasattr(self, 'playwright_directory') or self.playwright_directory is None else self.playwright_directory
				self.selenium_directory = os.path.join(self.results_directory, 'selenium') if not hasattr(self, 'selenium_directory') or self.selenium_directory is None else self.selenium_directory
				self.webdriverio_directory = os.path.join(self.results_directory, 'webdriverio') if not hasattr(self, 'webdriverio_directory') or self.webdriverio_directory is None else self.webdriverio_directory
				
				# Create all directories
				os.makedirs(self.excel_directory, exist_ok=True)
				os.makedirs(self.gherkin_directory, exist_ok=True)
				os.makedirs(self.playwright_directory, exist_ok=True)
				os.makedirs(self.selenium_directory, exist_ok=True)
				os.makedirs(self.webdriverio_directory, exist_ok=True)
				
				# Now generate artifacts
				await self.generate_master_excel()
				await self.generate_results_md()
				await self.generate_gherkin_code()
				await self.generate_playwright_code()
				await self.generate_selenium_code() 
				await self.generate_webdriverio_code()
			except Exception as e:
				loguru_logger.error(f"Error generating final artifacts: {str(e)}")
				# Try to create a minimal recovery file
				try:
					recovery_dir = os.path.join('organized', 'recovery')
					os.makedirs(recovery_dir, exist_ok=True)
					recovery_file = os.path.join(recovery_dir, f'error_report_{time.time()}.txt')
					with open(recovery_file, 'w') as f:
						f.write(f"Error generating artifacts: {str(e)}\n")
						f.write(f"Task: {self.task}\n")
						f.write(f"Steps: {self.state.n_steps}\n")
					loguru_logger.info(f"Created error report: {recovery_file}")
				except Exception as recovery_error:
					loguru_logger.error(f"Failed to create error report: {str(recovery_error)}")

	# @observe(name='controller.multi_act')
	@time_execution_async('--multi-act (agent)')
	async def multi_act(
		self,
		actions: list[ActionModel],
		check_for_new_elements: bool = True,
	) -> list[ActionResult]:
		"""Execute multiple actions"""
		results = []

		cached_selector_map = await self.browser_context.get_selector_map()
		cached_path_hashes = set(e.hash.branch_path_hash for e in cached_selector_map.values())

		await self.browser_context.remove_highlights()

		for i, action in enumerate(actions):
			if action.get_index() is not None and i != 0:
				new_state = await self.browser_context.get_state(cache_clickable_elements_hashes=False)
				new_selector_map = new_state.selector_map

				# Detect index change after previous action
				orig_target = cached_selector_map.get(action.get_index())  # type: ignore
				orig_target_hash = orig_target.hash.branch_path_hash if orig_target else None
				new_target = new_selector_map.get(action.get_index())  # type: ignore
				new_target_hash = new_target.hash.branch_path_hash if new_target else None
				if orig_target_hash != new_target_hash:
					msg = f'Element index changed after action {i} / {len(actions)}, because page changed.'
					loguru_logger.info(msg)
					results.append(ActionResult(extracted_content=msg, include_in_memory=True))
					break

				new_path_hashes = set(e.hash.branch_path_hash for e in new_selector_map.values())
				if check_for_new_elements and not new_path_hashes.issubset(cached_path_hashes):
					# next action requires index but there are new elements on the page
					msg = f'Something new appeared after action {i} / {len(actions)}'
					loguru_logger.info(msg)
					results.append(ActionResult(extracted_content=msg, include_in_memory=True))
					break

			try:
				await self._raise_if_stopped_or_paused()

				result = await self.controller.act(
					action,
					self.browser_context,
					self.settings.page_extraction_llm,
					self.sensitive_data,
					self.settings.available_file_paths,
					context=self.context,
				)

				results.append(result)

				loguru_logger.debug(f'Executed action {i + 1} / {len(actions)}')
				if results[-1].is_done or results[-1].error or i == len(actions) - 1:
					break

				# Add a delay between actions to ensure the browser has time to load elements
				await asyncio.sleep(1)

			except asyncio.CancelledError:
				# Gracefully handle task cancellation
				loguru_logger.info(f'Action {i + 1} was cancelled due to Ctrl+C')
				if not results:
					# Add a result for the cancelled action
					results.append(ActionResult(error='The action was cancelled due to Ctrl+C', include_in_memory=True))
				raise InterruptedError('Action cancelled by user')

		return results

	async def _validate_output(self) -> bool:
		"""Validate the output of the last action is what the user wanted"""
		system_msg = (
			f'You are a validator of an agent who interacts with a browser. '
			f'Validate if the output of last action is what the user wanted and if the task is completed. '
			f'If the task is unclear defined, you can let it pass. But if something is missing or the image does not show what was requested dont let it pass. '
			f'Try to understand the page and help the model with suggestions like scroll, do x, ... to get the solution right. '
			f'Task to validate: {self.task}. Return a JSON object with 2 keys: is_valid and reason. '
			f'is_valid is a boolean that indicates if the output is correct. '
			f'reason is a string that explains why it is valid or not.'
			f' example: {{"is_valid": false, "reason": "The user wanted to search for "cat photos", but the agent searched for "dog photos" instead."}}'
		)

		if self.browser_context.session:
			state = await self.browser_context.get_state(cache_clickable_elements_hashes=False)
			content = AgentMessagePrompt(
				state=state,
				result=self.state.last_result,
				include_attributes=self.settings.include_attributes,
			)
			msg = [SystemMessage(content=system_msg), content.get_user_message(self.settings.use_vision)]
		else:
			# if no browser session, we can't validate the output
			return True

		class ValidationResult(BaseModel):
			"""
			Validation results.
			"""

			is_valid: bool
			reason: str

		validator = self.llm.with_structured_output(ValidationResult, include_raw=True)
		response: dict[str, Any] = await validator.ainvoke(msg)  # type: ignore
		parsed: ValidationResult = response['parsed']
		is_valid = parsed.is_valid
		if not is_valid:
			loguru_logger.info(f'❌ Validator decision: {parsed.reason}')
			msg = f'The output is not yet correct. {parsed.reason}.'
			self.state.last_result = [ActionResult(extracted_content=msg, include_in_memory=True)]
		else:
			loguru_logger.info(f'✅ Validator decision: {parsed.reason}')
		return is_valid

	async def log_completion(self) -> None:
		"""Log the completion of the task"""
		loguru_logger.info('✅ Task completed')
		if self.state.history.is_successful():
			loguru_logger.info('✅ Successfully')
		else:
			loguru_logger.info('❌ Unfinished')

		total_tokens = self.state.history.total_input_tokens()
		loguru_logger.info(f'📝 Total input tokens used (approximate): {total_tokens}')

		if self.register_done_callback:
			if inspect.iscoroutinefunction(self.register_done_callback):
				await self.register_done_callback(self.state.history)
			else:
				self.register_done_callback(self.state.history)

	async def rerun_history(
		self,
		history: AgentHistoryList,
		max_retries: int = 3,
		skip_failures: bool = True,
		delay_between_actions: float = 2.0,
	) -> list[ActionResult]:
		"""
		Rerun a saved history of actions with error handling and retry logic.

		Args:
				history: The history to replay
				max_retries: Maximum number of retries per action
				skip_failures: Whether to skip failed actions or stop execution
				delay_between_actions: Delay between actions in seconds

		Returns:
				List of action results
		"""
		# Execute initial actions if provided
		if self.initial_actions:
			result = await self.multi_act(self.initial_actions)
			self.state.last_result = result

		results = []

		for i, history_item in enumerate(history.history):
			goal = history_item.model_output.current_state.next_goal if history_item.model_output else ''
			loguru_logger.info(f'Replaying step {i + 1}/{len(history.history)}: goal: {goal}')

			if (
				not history_item.model_output
				or not history_item.model_output.action
				or history_item.model_output.action == [None]
			):
				loguru_logger.warning(f'Step {i + 1}: No action to replay, skipping')
				results.append(ActionResult(error='No action to replay'))
				continue

			retry_count = 0
			while retry_count < max_retries:
				try:
					result = await self._execute_history_step(history_item, delay_between_actions)
					results.extend(result)
					break

				except Exception as e:
					retry_count += 1
					if retry_count == max_retries:
						error_msg = f'Step {i + 1} failed after {max_retries} attempts: {str(e)}'
						loguru_logger.error(error_msg)
						if not skip_failures:
							results.append(ActionResult(error=error_msg))
							raise RuntimeError(error_msg)
					else:
						loguru_logger.warning(f'Step {i + 1} failed (attempt {retry_count}/{max_retries}), retrying...')
						await asyncio.sleep(delay_between_actions)

		return results

	async def _execute_history_step(self, history_item: AgentHistory, delay: float) -> list[ActionResult]:
		"""Execute a single step from history with element validation"""
		state = await self.browser_context.get_state(cache_clickable_elements_hashes=False)
		if not state or not history_item.model_output:
			raise ValueError('Invalid state or model output')
		updated_actions = []
		for i, action in enumerate(history_item.model_output.action):
			updated_action = await self._update_action_indices(
				history_item.state.interacted_element[i],
				action,
				state,
			)
			updated_actions.append(updated_action)

			if updated_action is None:
				raise ValueError(f'Could not find matching element {i} in current page')

		result = await self.multi_act(updated_actions)

		await asyncio.sleep(delay)
		return result

	async def _update_action_indices(
		self,
		historical_element: Optional[DOMHistoryElement],
		action: ActionModel,  # Type this properly based on your action model
		current_state: BrowserState,
	) -> Optional[ActionModel]:
		"""
		Update action indices based on current page state.
		Returns updated action or None if element cannot be found.
		"""
		if not historical_element or not current_state.element_tree:
			return action

		current_element = HistoryTreeProcessor.find_history_element_in_tree(historical_element, current_state.element_tree)

		if not current_element or current_element.highlight_index is None:
			return None

		old_index = action.get_index()
		if old_index != current_element.highlight_index:
			action.set_index(current_element.highlight_index)
			loguru_logger.info(f'Element moved in DOM, updated index from {old_index} to {current_element.highlight_index}')

		return action

	async def load_and_rerun(self, history_file: Optional[str | Path] = None, **kwargs) -> list[ActionResult]:
		"""
		Load history from file and rerun it.

		Args:
				history_file: Path to the history file
				**kwargs: Additional arguments passed to rerun_history
		"""
		if not history_file:
			history_file = 'AgentHistory.json'
		history = AgentHistoryList.load_from_file(history_file, self.AgentOutput)
		return await self.rerun_history(history, **kwargs)

	def save_history(self, file_path: Optional[str | Path] = None) -> None:
		"""Save the history to a file"""
		if not file_path:
			file_path = 'AgentHistory.json'
		self.state.history.save_to_file(file_path)

	def pause(self) -> None:
		"""Pause the agent before the next step"""
		print('\n\n⏸️  Got Ctrl+C, paused the agent and left the browser open.')
		self.state.paused = True

		# The signal handler will handle the asyncio pause logic for us
		# No need to duplicate the code here

	def resume(self) -> None:
		"""Resume the agent"""
		print('----------------------------------------------------------------------')
		print('▶️  Got Enter, resuming agent execution where it left off...\n')
		self.state.paused = False

		# The signal handler should have already reset the flags
		# through its reset() method when called from run()

		# playwright browser is always immediately killed by the first Ctrl+C (no way to stop that)
		# so we need to restart the browser if user wants to continue
		if self.browser:
			loguru_logger.info('🌎 Restarting/reconnecting to browser...')
			loop = asyncio.get_event_loop()
			loop.create_task(self.browser._init())
			loop.create_task(asyncio.sleep(5))

	def stop(self) -> None:
		"""Stop the agent"""
		loguru_logger.info('⏹️ Agent stopping')
		self.state.stopped = True

	def _convert_initial_actions(self, actions: List[Dict[str, Dict[str, Any]]]) -> List[ActionModel]:
		"""Convert dictionary-based actions to ActionModel instances"""
		converted_actions = []
		action_model = self.ActionModel
		for action_dict in actions:
			# Each action_dict should have a single key-value pair
			action_name = next(iter(action_dict))
			params = action_dict[action_name]

			# Get the parameter model for this action from registry
			action_info = self.controller.registry.registry.actions[action_name]
			param_model = action_info.param_model

			# Create validated parameters using the appropriate param model
			validated_params = param_model(**params)

			# Create ActionModel instance with the validated parameters
			action_model = self.ActionModel(**{action_name: validated_params})
			converted_actions.append(action_model)

		return converted_actions

	async def _verify_llm_connection(self) -> bool:
		"""
		Verify that the LLM API keys are setup and the LLM API is responding properly.
		Helps prevent errors due to running out of API credits, missing env vars, or network issues.
		"""
		if getattr(self.llm, '_verified_api_keys', None) is True:
			return True  # If the LLM API keys have already been verified during a previous run, skip the test

		# Check if required environment variables are set for the model we're using
		required_keys = REQUIRED_LLM_API_ENV_VARS.get(self.llm.__class__.__name__, [])
		if required_keys and not check_env_variables(required_keys, any_or_all=all):
			error = f'LLM API Key environment variables not set up for {self.llm.__class__.__name__}, missing: {required_keys}'
			loguru_logger.warning(f'❌ {error}')
			if not SKIP_LLM_API_KEY_VERIFICATION:
				self.llm._verified_api_keys = False
				raise ValueError(error)

		if SKIP_LLM_API_KEY_VERIFICATION:  # skip roundtrip connection test for speed in cloud environment
			self.llm._verified_api_keys = True
			return True

		test_prompt = 'What is the capital of France? Respond with a single word.'
		test_answer = 'paris'
		try:
			response = await self.llm.ainvoke([HumanMessage(content=test_prompt)])
			response_text = str(response.content).lower()

			if test_answer in response_text:
				loguru_logger.debug(
					f'🧠 LLM API keys {", ".join(required_keys)} verified, {self.llm.__class__.__name__} model is connected and responding correctly.'
				)
				self.llm._verified_api_keys = True
				return True
			else:
				loguru_logger.debug(
					'❌  Got bad LLM response to basic sanity check question: \n\t  %s\n\t\tEXPECTING: %s\n\t\tGOT: %s',
					test_prompt,
					test_answer,
					response,
				)
				raise Exception('LLM responded to a simple test question incorrectly')
		except Exception as e:
			self.llm._verified_api_keys = False
			loguru_logger.error(
				f'\n\n❌  LLM {self.llm.__class__.__name__} connection test failed. Check that {", ".join(required_keys)} is set correctly in .env and that the LLM API account has sufficient funding.\n\n{e}\n'
			)
			raise Exception(f'LLM API connection test failed: {e}') from e

	async def _run_planner(self) -> Optional[str]:
		"""Run the planner to analyze state and suggest next steps"""
		# Skip planning if no planner_llm is set
		if not self.settings.planner_llm:
			return None

		# Get current state to filter actions by page
		page = await self.browser_context.get_current_page()

		# Get all standard actions (no filter) and page-specific actions
		standard_actions = self.controller.registry.get_prompt_description()  # No page = system prompt actions
		page_actions = self.controller.registry.get_prompt_description(page)  # Page-specific actions

		# Combine both for the planner
		all_actions = standard_actions
		if page_actions:
			all_actions += '\n' + page_actions

		# Create planner message history using full message history with all available actions
		planner_messages = [
			PlannerPrompt(all_actions).get_system_message(self.settings.is_planner_reasoning),
			*self._message_manager.get_messages()[1:],  # Use full message history except the first
		]

		if not self.settings.use_vision_for_planner and self.settings.use_vision:
			last_state_message: HumanMessage = planner_messages[-1]
			# remove image from last state message
			new_msg = ''
			if isinstance(last_state_message.content, list):
				for msg in last_state_message.content:
					if msg['type'] == 'text':  # type: ignore
						new_msg += msg['text']  # type: ignore
					elif msg['type'] == 'image_url':  # type: ignore
						continue  # type: ignore
			else:
				new_msg = last_state_message.content

			planner_messages[-1] = HumanMessage(content=new_msg)

		planner_messages = convert_input_messages(planner_messages, self.planner_model_name)

		# Get planner output
		try:
			response = await self.settings.planner_llm.ainvoke(planner_messages)
		except Exception as e:
			loguru_logger.error(f'Failed to invoke planner: {str(e)}')
			raise LLMException(401, 'LLM API call failed') from e

		plan = str(response.content)
		# if deepseek-reasoner, remove think tags
		if self.planner_model_name and (
			'deepseek-r1' in self.planner_model_name or 'deepseek-reasoner' in self.planner_model_name
		):
			plan = self._remove_think_tags(plan)
		try:
			plan_json = json.loads(plan)
			loguru_logger.info(f'Planning Analysis:\n{json.dumps(plan_json, indent=4)}')
		except json.JSONDecodeError:
			loguru_logger.info(f'Planning Analysis:\n{plan}')
		except Exception as e:
			loguru_logger.debug(f'Error parsing planning analysis: {e}')
			loguru_logger.info(f'Plan: {plan}')

		return plan

	@property
	def message_manager(self) -> MessageManager:
		return self._message_manager

	async def close(self):
		"""Close all resources"""
		try:
			# First close browser resources
			if self.browser_context and not self.injected_browser_context:
				await self.browser_context.close()
			if self.browser and not self.injected_browser:
				await self.browser.close()

			# Force garbage collection
			gc.collect()

		except Exception as e:
			loguru_logger.error(f'Error during cleanup: {e}')

	async def _update_action_models_for_page(self, page) -> None:
		"""Update action models with page-specific actions"""
		# Create new action model with current page's filtered actions
		self.ActionModel = self.controller.registry.create_action_model(page=page)
		# Update output model with the new actions
		self.AgentOutput = AgentOutput.type_with_custom_actions(self.ActionModel)

		# Update done action model too
		self.DoneActionModel = self.controller.registry.create_action_model(include_actions=['done'], page=page)
		self.DoneAgentOutput = AgentOutput.type_with_custom_actions(self.DoneActionModel)

	# Function to generate master Excel file
	async def generate_master_excel(self):
		# Example data, replace with actual data
		data = {
			'Step': [1, 2, 3],
			'Action': ['Login', 'Add to Cart', 'Checkout'],
			'Status': ['Success', 'Success', 'Failed']
		}
		df = pd.DataFrame(data)
		excel_path = os.path.join(self.excel_directory, 'master.xlsx')
		df.to_excel(excel_path, index=False)
		loguru_logger.info(f'Master Excel file generated at {excel_path}')

	# Function to generate results.md
	async def generate_results_md(self):
		# Determine task success
		task_success = self.state.history.is_successful()
		task_status = 'Success' if task_success else 'Failed'

		# Generate Markdown content
		md_content = f"""
# Task Results

## Summary
- **Task**: {self.task}
- **Steps Completed**: {self.state.n_steps}
- **Overall Status**: {task_status}

## Details
"""

		# Add step details
		for i, action in enumerate(self.state.history.model_actions()):
			# Determine step status based on the 'success' field in the action's result
			# Ensure 'success' is checked correctly
			step_status = 'Success' if action.get('success', False) else 'Failed'
			interacted_element = action.get('interacted_element')
			# Access tag_name directly from DOMHistoryElement
			tag_name = interacted_element.tag_name if interacted_element else 'Unknown'
			md_content += f"- Step {i + 1}: {tag_name} - {step_status}\n"

		# Write to results.md
		md_path = os.path.join(self.results_directory, 'results.md')
		with open(md_path, 'w') as md_file:
			md_file.write(md_content)
		loguru_logger.info(f'Results Markdown file generated at {md_path}')

	async def generate_webdriverio_code(self):
		"""Generate WebdriverIO test code based on the agent's actions."""
		try:
			# Check and initialize webdriverio directory
			if not hasattr(self, 'webdriverio_directory') or self.webdriverio_directory is None:
				loguru_logger.warning('webdriverio_directory was not initialized, creating default directory')
				self.webdriverio_directory = os.path.join(self.results_directory, 'webdriverio')
			
			# Create directory if it doesn't exist
			os.makedirs(self.webdriverio_directory, exist_ok=True)
			
			# Create WebdriverIO test file content
			code_content = f"""// WebdriverIO test script for: {self.sanitize_text(self.task)}
// Generated from agent execution history

describe('{self.sanitize_text(self.task)}', () => {{{{
    it('should automate the task', async function() {{{{
        // Set a reasonable timeout for the test
        this.timeout(30000);
        
"""
			
			# Add test steps based on agent's history
			for i, history_item in enumerate(self.state.history.history):
				if not history_item.model_output or not history_item.model_output.action:
					continue
				
				for action in history_item.model_output.action:
					action_type = next(iter(action.model_dump(exclude_unset=True).keys()), "unknown")
					action_params = next(iter(action.model_dump(exclude_unset=True).values()), {})
					
					if action_type == "go_to_url" and "url" in action_params:
						code_content += f"""        // Step {i+1}: Navigate to URL
        await browser.url('{action_params['url']}');
        console.log('Navigated to {action_params['url']}');
        await browser.pause(1000); // Wait for page to load
        
"""
					elif action_type == "click_element_by_index" and "index" in action_params:
						# Try to get element details
						selector = ""
						desc = f"element with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'selector'):
								selector = elem.selector
								desc = f"{getattr(elem, 'tag_name', 'element')} with selector '{selector}'"
						
						if selector:
							code_content += f"""        // Step {i+1}: Click on {desc}
        const element{i} = await $('{selector}');
        await element{i}.waitForClickable();
        await element{i}.click();
        console.log('Clicked on {desc}');
        await browser.pause(1000); // Wait for any page changes
        
"""
						else:
							code_content += f"""        // Step {i+1}: Click on {desc}
        // Could not determine selector, this step may require manual implementation
        console.log('WARNING: Could not determine selector for click operation');
        
"""
					elif action_type == "input_text" and "index" in action_params and "text" in action_params:
						# Try to get element details
						selector = ""
						desc = f"input field with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'selector'):
								selector = elem.selector
								desc = f"input field with selector '{selector}'"
						
						if selector:
							code_content += f"""        // Step {i+1}: Input text into {desc}
        const input{i} = await $('{selector}');
        await input{i}.waitForExist();
        await input{i}.setValue('{action_params['text']}');
        console.log('Entered text: \\'{action_params['text']}\\' into {desc}');
        
"""
						else:
							code_content += f"""        // Step {i+1}: Input text into {desc}
        // Could not determine selector, this step may require manual implementation
        console.log('WARNING: Could not determine selector for input operation');
        
"""
					elif action_type == "extract_text" and "index" in action_params:
						# Try to get element details
						selector = ""
						desc = f"element with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'selector'):
								selector = elem.selector
								desc = f"{getattr(elem, 'tag_name', 'element')} with selector '{selector}'"
						
						if selector:
							code_content += f"""        // Step {i+1}: Extract text from {desc}
        const textElement{i} = await $('{selector}');
        await textElement{i}.waitForExist();
        const extractedText{i} = await textElement{i}.getText();
        console.log("Extracted text: '" + extractedText{i} + "' from {desc}");
        
"""
						else:
							code_content += f"""        // Step {i+1}: Extract text from {desc}
        // Could not determine selector, this step may require manual implementation
        console.log('WARNING: Could not determine selector for text extraction');
        
"""
					elif action_type == "done":
						success = action_params.get("success", False)
						extracted = action_params.get("extracted_content", "").replace("\n", " ")
						code_content += f"""        // Final step: Task completion
        console.log('Task {"completed successfully" if success else "ended but was not successful"}');
        """
						if extracted:
							code_content += f"""
        console.log('Final result: {extracted[:100]}{"..." if len(extracted) > 100 else ""}');
        """
			
			# Close the test function - using double curly braces to escape them in f-strings
			code_content += """    }});
    
    afterEach(async function() {
        // Take screenshot if test fails
        if (this.currentTest.state === 'failed') {
            await browser.saveScreenshot("./error-" + new Date().getTime() + ".png");
        }
    }});
}});
"""
			
			# Write to file with explicit path check
			webdriverio_path = os.path.join(self.webdriverio_directory, 'test.js')
			with open(webdriverio_path, 'w', encoding='utf-8') as f:
				f.write(code_content)
			loguru_logger.info(f'WebdriverIO test code generated at {webdriverio_path}')
			return webdriverio_path
		except Exception as e:
			loguru_logger.error(f'Error generating WebdriverIO code: {str(e)}')
			
			# Attempt recovery if there are path issues
			try:
				# Ensure we have a valid recovery directory path
				recovery_directory = os.path.join('organized', 'recovery', 'webdriverio')
				os.makedirs(recovery_directory, exist_ok=True)
				recovery_path = os.path.join(recovery_directory, 'test.js')
				
				with open(recovery_path, 'w', encoding='utf-8') as f:
					f.write("// Error during generation - this is a recovery file\n")
				
				loguru_logger.info(f'Created recovery WebdriverIO file at {recovery_path}')
				return recovery_path
			except Exception as recovery_error:
				loguru_logger.error(f'Failed even recovery attempt: {str(recovery_error)}')
				return None

	def sanitize_text(self, text):
		"""Sanitize text by escaping special characters for inclusion in code."""
		if text is None:
			return ""
		
		# Convert to string if needed
		text = str(text)
		
		# Replace common problematic characters 
		replacements = {
			"'": "\\'",    # Single quotes
			'"': '\\"',    # Double quotes 
			"\n": "\\n",   # Newlines
			"\r": "\\r",   # Carriage returns
			"\t": "\\t",   # Tabs
			"\\": "\\\\",  # Backslash itself
		}
		
		# Apply replacements
		for char, replacement in replacements.items():
			text = text.replace(char, replacement)
			
		return text

	async def generate_gherkin_code(self) -> None:
		"""Generate Gherkin feature file for the agent's execution history"""
		try:
			# Initialize variables
			self.gherkin_directory = os.path.join(self.results_directory, 'gherkin')
			os.makedirs(self.gherkin_directory, exist_ok=True)
			
			# Generate feature file content
			code_content = f"Feature: {self.sanitize_text(self.task)}\n"
			code_content += "  As a user\n"
			code_content += "  I want to automate browser interactions\n"
			code_content += "  So that I can achieve my task without manual intervention\n\n"
			
			# Create a scenario based on the task
			code_content += f"  Scenario: {self.sanitize_text(self.task)}\n"
			
			# Add steps based on agent's history
			for i, history_item in enumerate(self.state.history.history):
				if not history_item.model_output or not history_item.model_output.action:
					continue
				
				for action in history_item.model_output.action:
					action_type = next(iter(action.model_dump(exclude_unset=True).keys()), "unknown")
					action_params = next(iter(action.model_dump(exclude_unset=True).values()), {})
					
					if action_type == "go_to_url" and "url" in action_params:
						code_content += f"    Given I navigate to \"{action_params['url']}\"\n"
					
					elif action_type == "click_element_by_index" and "index" in action_params:
						# Try to get element details
						desc = f"element with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'tag_name'):
								tag_name = elem.tag_name
								desc = f"{tag_name}"
								if hasattr(elem, 'text') and elem.text:
									desc += f" containing \"{elem.text}\""
						
						code_content += f"    When I click on the {desc}\n"
					
					elif action_type == "input_text" and "index" in action_params and "text" in action_params:
						# Try to get element details
						desc = f"input field with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'tag_name'):
								tag_name = elem.tag_name
								desc = f"{tag_name}"
								if hasattr(elem, 'placeholder') and elem.placeholder:
									desc += f" with placeholder \"{elem.placeholder}\""
								elif hasattr(elem, 'name') and elem.name:
									desc += f" with name \"{elem.name}\""
						
						code_content += f"    And I enter \"{action_params['text']}\" into the {desc}\n"
					
					elif action_type == "extract_text" and "index" in action_params:
						# Try to get element details
						desc = f"element with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'tag_name'):
								tag_name = elem.tag_name
								desc = f"{tag_name}"
						
						code_content += f"    Then I should see text in the {desc}\n"
					
					elif action_type == "done":
						success = action_params.get("success", False)
						if success:
							code_content += "    Then I should see that the task is complete\n"
						else:
							code_content += "    But I am unable to complete the task\n"
			
			# Write to file
			feature_path = os.path.join(self.gherkin_directory, 'feature.feature')
			with open(feature_path, 'w', encoding='utf-8') as f:
				f.write(code_content)
			
			loguru_logger.info(f'Gherkin feature file generated at {feature_path}')
		except Exception as e:
			loguru_logger.error(f'Error generating Gherkin code: {str(e)}')
			# Create recovery file
			recovery_file = os.path.join(
				self.logs_directory, f'{self.state.agent_id}_gherkin_recovery_{time.time()}.feature'
			)
			with open(recovery_file, 'w') as f:
				f.write(f'# Error occurred during Gherkin generation\n# {str(e)}\n\n{code_content}')
			loguru_logger.info(f'Created recovery file: {recovery_file}')

	async def generate_selenium_code(self) -> None:
		"""Generate Selenium test code for the agent's execution history"""
		try:
			# Ensure selenium directory exists
			self.selenium_directory = os.path.join(self.results_directory, 'selenium')
			os.makedirs(self.selenium_directory, exist_ok=True)

			# Generate code content
			code_content = "const { Builder, By, Key, until } = require('selenium-webdriver');\n"
			code_content += "const chrome = require('selenium-webdriver/chrome');\n"
			code_content += "const assert = require('assert');\n\n"
			
			code_content += "describe('Generated Selenium Test', function() {\n"
			code_content += "  this.timeout(30000);\n"
			code_content += "  let driver;\n\n"
			
			code_content += "  beforeEach(async function() {\n"
			code_content += "    driver = await new Builder()\n"
			code_content += "      .forBrowser('chrome')\n"
			code_content += "      .setChromeOptions(new chrome.Options().headless())\n"
			code_content += "      .build();\n"
			code_content += "  });\n\n"
			
			code_content += "  afterEach(async function() {\n"
			code_content += "    if (driver) {\n"
			code_content += "      await driver.quit();\n"
			code_content += "    }\n"
			code_content += "  });\n\n"
			
			code_content += "  it('completes the task', async function() {\n"
			code_content += "    try {\n"
            
			# Add task description
			code_content += f"      // Task: {self.sanitize_text(self.task)}\n"

			# Add steps based on agent's history
			for history_item in self.state.history.history:
				if not history_item.model_output or not history_item.model_output.action:
					continue
				
				for action in history_item.model_output.action:
					action_type = next(iter(action.model_dump(exclude_unset=True).keys()), "unknown")
					action_params = next(iter(action.model_dump(exclude_unset=True).values()), {})
					
					if action_type == "go_to_url" and "url" in action_params:
						code_content += f"      // Navigate to {action_params['url']}\n"
						code_content += f"      await driver.get('{self.sanitize_text(action_params['url'])}');\n"
					
					elif action_type == "click_element_by_index" and "index" in action_params:
						# Try to get element details
						selector = ""
						desc = f"element with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'selector'):
								selector = elem.selector
								desc = f"{getattr(elem, 'tag_name', 'element')} with selector '{selector}'"
						
						if selector:
							code_content += f"      // Click on {desc}\n"
							code_content += f"      await driver.wait(until.elementLocated(By.css('{self.sanitize_text(selector)}')), 10000);\n"
							code_content += f"      await driver.findElement(By.css('{self.sanitize_text(selector)}')).click();\n"
						else:
							code_content += f"      // Click on {desc} (selector not determined)\n"
							code_content += f"      // WARNING: Manual implementation required\n"
					
					elif action_type == "input_text" and "index" in action_params and "text" in action_params:
						# Try to get element details
						selector = ""
						desc = f"input field with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'selector'):
								selector = elem.selector
								desc = f"input field with selector '{selector}'"
						
						if selector:
							code_content += f"      // Input text into {desc}\n"
							code_content += f"      await driver.wait(until.elementLocated(By.css('{self.sanitize_text(selector)}')), 10000);\n"
							code_content += f"      const inputElement = await driver.findElement(By.css('{self.sanitize_text(selector)}'));\n"
							code_content += f"      await inputElement.clear();\n"
							code_content += f"      await inputElement.sendKeys('{self.sanitize_text(action_params['text'])}');\n"
						else:
							code_content += f"      // Input text into {desc} (selector not determined)\n"
							code_content += f"      // WARNING: Manual implementation required\n"
					
					elif action_type == "extract_text" and "index" in action_params:
						# Try to get element details
						selector = ""
						desc = f"element with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'selector'):
								selector = elem.selector
								desc = f"{getattr(elem, 'tag_name', 'element')} with selector '{selector}'"
						
						if selector:
							code_content += f"      // Extract text from {desc}\n"
							code_content += f"      await driver.wait(until.elementLocated(By.css('{self.sanitize_text(selector)}')), 10000);\n"
							code_content += f"      const extractedText = await driver.findElement(By.css('{self.sanitize_text(selector)}')).getText();\n"
							code_content += f"      console.log('Extracted text:', extractedText);\n"
						else:
							code_content += f"      // Extract text from {desc} (selector not determined)\n"
							code_content += f"      // WARNING: Manual implementation required\n"
					
					elif action_type == "done":
						code_content += f"      // Task completed\n"
						code_content += f"      console.log('Task completed successfully');\n"

			code_content += "    } catch (error) {\n"
			code_content += "      // Take screenshot on failure\n"
			code_content += "      if (driver) {\n"
			code_content += "        const screenshotData = await driver.takeScreenshot();\n"
			code_content += "        require('fs').writeFileSync('error-screenshot.png', screenshotData, 'base64');\n"
			code_content += "      }\n"
			code_content += "      throw error;\n"
			code_content += "    }\n"
			code_content += "  });\n"
			code_content += "});\n"

			# Write to file
			output_path = os.path.join(self.selenium_directory, 'test.js')
			with open(output_path, 'w') as f:
				f.write(code_content)
			
			loguru_logger.info(f'✅ Generated Selenium test code: {output_path}')
		
		except Exception as e:
			loguru_logger.error(f'Error generating Selenium code: {str(e)}')
			# Create recovery file
			# Check if logs_directory exists
			if hasattr(self, 'logs_directory') and self.logs_directory:
				recovery_file = os.path.join(
					self.logs_directory, f'{self.state.agent_id}_selenium_recovery_{time.time()}.js'
				)
				try:
					with open(recovery_file, 'w') as f:
						f.write(f'// Error occurred during Selenium code generation\n// {str(e)}\n\n{code_content}')
					loguru_logger.info(f'Created recovery file: {recovery_file}')
				except Exception as inner_e:
					loguru_logger.error(f'Failed to create recovery file: {str(inner_e)}')
			else:
				# If logs_directory doesn't exist, use a default path
				try:
					default_dir = os.path.join('organized', 'logs')
					os.makedirs(default_dir, exist_ok=True)
					recovery_file = os.path.join(
						default_dir, f'selenium_recovery_{time.time()}.js'
					)
					with open(recovery_file, 'w') as f:
						f.write(f'// Error occurred during Selenium code generation\n// {str(e)}\n\n{code_content}')
					loguru_logger.info(f'Created recovery file (fallback): {recovery_file}')
				except Exception as inner_e:
					loguru_logger.error(f'Failed to create recovery file (fallback): {str(inner_e)}')
	async def generate_playwright_code(self) -> None:
		"""Generate Playwright test code for the agent's execution history"""
		try:
			# Initialize variables
			self.playwright_directory = os.path.join(self.results_directory, 'playwright')
			os.makedirs(self.playwright_directory, exist_ok=True)
			
			# Generate code content
			code_content = "// Playwright test script\n"
			code_content += "const { test, expect } = require('@playwright/test');\n\n"
			
			# Remove backticks and fix JavaScript template syntax with proper Python f-string
			code_content += f"test('{self.sanitize_text(self.task)}', async ({{ page }}) => {{\n"
			code_content += "  // Set timeout for entire test\n"
			code_content += "  test.setTimeout(30000);\n\n"
			
			# Add test steps based on agent's history
			for i, history_item in enumerate(self.state.history.history):
				if not history_item.model_output or not history_item.model_output.action:
					continue
				
				for action in history_item.model_output.action:
					action_type = next(iter(action.model_dump(exclude_unset=True).keys()), "unknown")
					action_params = next(iter(action.model_dump(exclude_unset=True).values()), {})
					
					if action_type == "go_to_url" and "url" in action_params:
						code_content += f"  // Step {i+1}: Navigate to URL\n"
						code_content += f"  await page.goto('{action_params['url']}');\n"
						code_content += f"  console.log('Navigated to {action_params['url']}');\n"
						code_content += "  await page.waitForLoadState('networkidle');\n\n"
					
					elif action_type == "click_element_by_index" and "index" in action_params:
						# Try to get element details
						selector = ""
						desc = f"element with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'selector'):
								selector = elem.selector
								desc = f"{getattr(elem, 'tag_name', 'element')} with selector '{selector}'"
						
						if selector:
							code_content += f"  // Step {i+1}: Click on {desc}\n"
							code_content += f"  await page.waitForSelector('{selector}');\n"
							code_content += f"  await page.click('{selector}');\n"
							code_content += f"  console.log('Clicked on {desc}');\n\n"
						else:
							code_content += f"  // Step {i+1}: Click on {desc}\n"
							code_content += "  // Could not determine selector, this step may require manual implementation\n"
							code_content += "  console.warn('Could not determine selector for click operation');\n\n"
					
					elif action_type == "input_text" and "index" in action_params and "text" in action_params:
						# Try to get element details
						selector = ""
						desc = f"input field with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'selector'):
								selector = elem.selector
								desc = f"input field with selector '{selector}'"
						
						if selector:
							code_content += f"  // Step {i+1}: Input text into {desc}\n"
							code_content += f"  await page.waitForSelector('{selector}');\n"
							code_content += f"  await page.fill('{selector}', '{action_params['text']}');\n"
							code_content += f"  console.log('Entered text: \"{action_params['text']}\" into {desc}');\n\n"
						else:
							code_content += f"  // Step {i+1}: Input text into {desc}\n"
							code_content += "  // Could not determine selector, this step may require manual implementation\n"
							code_content += "  console.warn('Could not determine selector for input operation');\n\n"
					
					elif action_type == "extract_text" and "index" in action_params:
						# Try to get element details
						selector = ""
						desc = f"element with index {action_params['index']}"
						
						if history_item.state and history_item.state.interacted_element and history_item.state.interacted_element[0]:
							elem = history_item.state.interacted_element[0]
							if hasattr(elem, 'selector'):
								selector = elem.selector
								desc = f"{getattr(elem, 'tag_name', 'element')} with selector '{selector}'"
						
						if selector:
							code_content += f"  // Step {i+1}: Extract text from {desc}\n"
							code_content += f"  await page.waitForSelector('{selector}');\n"
							code_content += f"  const extractedText{i} = await page.textContent('{selector}');\n"
							code_content += f"  console.log('Extracted text:', extractedText{i});\n\n"
						else:
							code_content += f"  // Step {i+1}: Extract text from {desc}\n"
							code_content += "  // Could not determine selector, this step may require manual implementation\n"
							code_content += "  console.warn('Could not determine selector for text extraction');\n\n"
					
					elif action_type == "done":
						success = action_params.get("success", False)
						code_content += "  // Final step: Task completion\n"
						if success:
							code_content += "  console.log('Task completed successfully');\n\n"
						else:
							code_content += "  console.log('Task ended but was not successful');\n\n"
			
			# Close the test function
			code_content += "  // Take screenshot at the end\n"
			code_content += "  await page.screenshot({ path: 'final-state.png' });\n"
			code_content += "});\n"
			
			# Write to file
			test_path = os.path.join(self.playwright_directory, 'test.spec.js')
			with open(test_path, 'w', encoding='utf-8') as f:
				f.write(code_content)
			
			loguru_logger.info(f'Playwright test code generated at {test_path}')
		except Exception as e:
			loguru_logger.error(f'Error generating Playwright code: {str(e)}')
			# Create recovery file
			recovery_file = os.path.join(
				self.logs_directory, f'{self.state.agent_id}_playwright_recovery_{time.time()}.js'
			)
			try:
				with open(recovery_file, 'w') as f:
					f.write(f'// Error occurred during Playwright code generation\n// {str(e)}\n\n{code_content}')
				loguru_logger.info(f'Created recovery file: {recovery_file}')
			except Exception as inner_e:
				loguru_logger.error(f'Failed to create recovery file: {str(inner_e)}')
			
