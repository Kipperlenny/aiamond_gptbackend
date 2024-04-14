# AIamond GPT Backend

This is a Serverless application that uses AWS Lambda and the OpenAI GPT model.

## Prerequisites

- Node.js and npm
- Python 3.11
- Serverless Framework
- AWS CLI
- Git

## Installation

```bash
git clone https://github.com/Kipperlenny/aiamond_gptbackend.git
cd aiamond_gptbackend
npm install -g serverless
pip install -r requirements.txt
npx dotenv -e .env -- serverless deploy
```

## Usage

After deploying, you can call your API Gateway endpoint with a POST request to interact with the GPT model.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[GPL 3.0](https://choosealicense.com/licenses/gpl-3.0/)

