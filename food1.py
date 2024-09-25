from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = "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"

# Initial messages
messages = [
    {
        "role": "system",
        "content": "You are a medical assistant who works as a doctor. You have extensive knowledge about allergies, dietary restrictions, and serious health conditions. Users will provide ingredients and any allergies or health conditions they have. Your response should always start with either 'No' or 'Yes' if it's a question, then provide a brief explanation (in 3 lines) and suggest a moderation amount if the food can be eaten occasionally. Also, provide a link to a blog or article supporting your advice."
    },
    {
        "role": "assistant",
        "content": "Hey, how can I help you today?"
    }
]

@app.route('/')
def index():
    return render_template('templates/index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    messages.append({"role": "user", "content": user_input})
    
    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    assistant_reply = chat_completion.choices[0].message['content']
    messages.append({"role": "assistant", "content": assistant_reply})
    
    return jsonify({"reply": assistant_reply})

if __name__ == '__main__':
    app.run(debug=True)
