from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import base64
from PIL import Image
import pytesseract
import openai

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = "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"

# Directory to save images
SAVE_DIR = "/Users/amoggha03/Desktop/College/HACKS/FoodHealthBot/IMAGES"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# Predefined medical and allergy information
predefined_allergies = "nil"
predefined_medical_conditions = "nil"
personalDetails = ""

# Variables to store extracted text
extractedText1 = ""
extractedText2 = ""

# Initial messages for the chatbot
messages = [
    {
        "role": "system",
        "content": (
            f"You are a medical assistant who works as a doctor. You have extensive knowledge about allergies, "
            f"dietary restrictions, and serious health conditions. Users will provide their personal details- Age, weight and height and also any allergies or medical health conditions "
            f"they have. Your response should always start with either 'No' or 'Yes' if it's a question, then provide a brief explanation (in 3 lines) "
            f"and suggest a moderation amount if the food can be eaten occasionally. Also, provide a link to a blog or article supporting your advice."
            f" Personal details: {personalDetails}. Predefined allergies: {predefined_allergies}. Predefined medical conditions: {predefined_medical_conditions}. "
        )
    },
    {
        "role": "assistant",
        "content": "Hey, how can I help you today?"
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/saveImage', methods=['POST'])
def save_image():
    data = request.json
    allergy_report = data.get('allergyReport', '')
    medical_report = data.get('medicalReport', '')
    personal_details = data.get('personalDetails', '')
    extracted_text1 = data.get('extractedText1', '')
    extracted_text2 = data.get('extractedText2', '')

    combined_text = f"Personal Details: {personal_details}\nAllergies: {extracted_text1}\nMedical Info: {extracted_text2}"
    print(f"Combined Text Received in Flask: {combined_text}")
    global extractedText1, extractedText2, personalDetails

    try:
        allergyReport = request.json.get('allergyReport')
        medicalReport = request.json.get('medicalReport')
        personalDetails = request.json.get('personalDetails')  # Make sure this updates globally

        if allergyReport:
            image_data1 = allergyReport.split(',')[1]
            image_data1 = base64.b64decode(image_data1)
            image_path1 = os.path.join(SAVE_DIR, 'allergy_report.jpg')
            with open(image_path1, 'wb') as f:
                f.write(image_data1)
            extractedText1 = extract_text_from_image(image_path1)
            print("\nExtracted Allergy Report Text:", extractedText1)
        
        if medicalReport:
            image_data2 = medicalReport.split(',')[1]
            image_data2 = base64.b64decode(image_data2)
            image_path2 = os.path.join(SAVE_DIR, 'medical_report.jpg')
            with open(image_path2, 'wb') as f:
                f.write(image_data2)
            extractedText2 = extract_text_from_image(image_path2)
            print("\nExtracted Medical Report Text:", extractedText2)

        # Combine the extracted text with predefined information
        

        return jsonify({'success': True, 'extracted_text1': extractedText1, 'extracted_text2': extractedText2}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ingredients', methods=['POST'])
def ingredients():
    try:
        # Get ingredients from the request
        ingredients = request.json.get('ingredients')
        print("Ingredients:", ingredients)

        # Save ingredients as a text file
        directory = os.path.join(SAVE_DIR, 'ingredients.txt')
        with open(directory, 'w') as f:
            f.write(ingredients)

        # Extract text from the saved file
        extracted_text = extract_text_from_text_file(directory)
        print("\n\n\n\n\nExtracted Text:", extracted_text)

        # Handle medical info extraction from saved medical report images
        medical_info = extract_medical_info(extracted_text)
        print("\n\n\n\n\nMedical Info:", medical_info)

        # Add predefined medical and allergy information to the extracted text
        combined_text = (
            f"Predefined allergies: {predefined_allergies}. "
            f"Predefined medical conditions: {predefined_medical_conditions}. "
            f"Personal details: {personalDetails}. "
            f"Allergy_report: {extracted_text}. "
            f"MedicalInfo: {medical_info}"
        )
        print("\n\n\n\n\nCombined Text:", combined_text)

        # Send combined text to GPT for analysis
        ingredient_analysis = analyze_ingredients(combined_text)
        print("\n\n\n\n\nIngredient Analysis:", ingredient_analysis)

        return jsonify({'success': True, 'extracted_text': extracted_text, 'ingredient_analysis': ingredient_analysis}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

def extract_text_from_text_file(file_path):
    with open(file_path, 'r') as f:
        extracted_text = f.read()
    return extracted_text

@app.route('/chat', methods=['POST'])
def chat():
    global messages, personalDetails, extractedText1, extractedText2

    try:
        user_message = request.json.get('message')

        # Construct the prompt with predefined medical information and user message
        combined_text = (
            f"Predefined allergies: {predefined_allergies}. "
            f"Predefined medical conditions: {predefined_medical_conditions}. "
            f"Personal details: {personalDetails}. "
            f"Allergy report text: {extractedText1}. "
            f"Medical report text: {extractedText2}. "
            f"User query: {user_message}"
        )
        
        # Log the combined text and user message for debugging
        print("\nUser Message:", user_message)
        print("\nCombined Text Sent to GPT:", combined_text)

        # Adding user message to messages history
        messages.append({"role": "user", "content": user_message})

        # Chat completion request
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "You are a medical assistant with knowledge about allergies, dietary restrictions, and serious health conditions. "
                    "You must consider the user's predefined allergies, medical conditions, and personal details while formulating responses."
                )},
                {"role": "user", "content": combined_text}
            ]
        )

        # Extract the assistant's reply
        assistant_reply = chat_completion.choices[0].message['content']
        messages.append({"role": "assistant", "content": assistant_reply})

        # Log the assistant's reply for debugging
        print("\nAssistant Reply:", assistant_reply)

        return jsonify({'success': True, 'reply': assistant_reply}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

def extract_text_from_image(image_path):
    img = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(img)
    return extracted_text

def extract_medical_info(combined_text):
    # Placeholder for extracting medical information
    # Implement your own logic to handle combined_text
    # For now, we will simulate with dummy information
    return "Simulated medical info from combined text."

@app.route('/saveCombinedText', methods=['POST'])
def save_combined_text():
    global personalDetails, extractedText1, extractedText2

    try:
        data = request.json

        # Extract and update personal details
        personal_details = data.get('personalDetails', {})
        weight = personal_details.get('weight', '')
        age = personal_details.get('age', '')
        height = personal_details.get('height', '')

        # Update the global personalDetails variable
        personalDetails = f"Weight: {weight} kg, Age: {age} years, Height: {height} cm"

        # Extract and update allergy and medical info
        extractedText1 = data.get('allergyInput', '')
        extractedText2 = data.get('medicalInfoInput', '')

        # Log the updated values for debugging
        print("\nUpdated Personal Details:", personalDetails)
        print("Updated Allergy Report:", extractedText1)
        print("Updated Medical Info:", extractedText2)

        return jsonify({'success': True}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500



def extract_text_from_image(image_path):
    img = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(img)
    return extracted_text


@app.route('/input', methods=['POST'])
def get_input():
    x = request.form['x']
    y = request.form['y']
    return redirect(url_for('askme'))

@app.route('/askme')
def askme():
    return render_template('askme.html')
@app.route('/updatePersonalDetails', methods=['POST'])
def update_personal_details():
    global personalDetails
    
    try:
        data = request.json
        personalDetails = data.get('personalDetails', '')

        # Log the updated personal details for debugging
        print("\nUpdated Personal Details:", personalDetails)

        return jsonify({'success': True}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)