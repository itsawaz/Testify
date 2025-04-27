# Testify
This project provides an automated browser testing solution that uses AI to generate and execute tests for web applications.

## Features

- Automated browser testing with Playwright
- AI-driven test generation
- Real-time test progress monitoring
- Export tests to Playwright, Selenium, and Gherkin formats
- Comprehensive test reporting with screenshots

## Setup

1. Clone the repository:
```
git clone <repository-url>
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Configure your Azure OpenAI API keys in app.py:
```python
llm = AzureChatOpenAI(
    model="gpt-4o",
    api_version='2024-10-21',
    azure_endpoint='your endpoint', 
    api_key='your api key',
)
```

4. Run the application:
```
python app.py
```

## Usage

1. Open your browser and navigate to http://localhost:5000
2. Enter the URL of the website you want to test
3. Describe the testing task
4. Click "Run Test" to start the automated testing process
5. View real-time progress and results in the UI
6. Download test reports and export to different formats

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
