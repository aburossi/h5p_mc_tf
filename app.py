import streamlit as st
import json
import uuid
import zipfile
import io
import logging
from pathlib import Path

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Function to generate a unique UUID
def generate_uuid():
    return str(uuid.uuid4())

# Function to map MultipleChoice questions to H5P format
def map_multiple_choice(question):
    try:
        h5p_question = {
            "library": "H5P.MultiChoice 1.16",
            "params": {
                "question": question.get("question", "Keine Frage gestellt."),
                "answers": [],
                "behaviour": {
                    "singleAnswer": True,
                    "enableRetry": False,
                    "enableSolutionsButton": False,
                    "enableCheckButton": True,
                    "type": "auto",
                    "singlePoint": False,
                    "randomAnswers": True,  # This will be controlled globally
                    "showSolutionsRequiresInput": True,
                    "confirmCheckDialog": False,
                    "confirmRetryDialog": False,
                    "autoCheck": False,
                    "passPercentage": 100,
                    "showScorePoints": True
                },
                "media": {
                    "disableImageZooming": False
                },
                "overallFeedback": [
                    {
                        "from": 0,
                        "to": 100
                    }
                ],
                "UI": {
                    "checkAnswerButton": "Überprüfen",
                    "submitAnswerButton": "Absenden",
                    "showSolutionButton": "Lösung anzeigen",
                    "tryAgainButton": "Wiederholen",
                    "tipsLabel": "Hinweis anzeigen",
                    "scoreBarLabel": "Du hast :num von :total Punkten erreicht.",
                    "tipAvailable": "Hinweis verfügbar",
                    "feedbackAvailable": "Rückmeldung verfügbar",
                    "readFeedback": "Rückmeldung vorlesen",
                    "wrongAnswer": "Falsche Antwort",
                    "correctAnswer": "Richtige Antwort",
                    "shouldCheck": "Hätte gewählt werden müssen",
                    "shouldNotCheck": "Hätte nicht gewählt werden sollen",
                    "noInput": "Bitte antworte, bevor du die Lösung ansiehst",
                    "a11yCheck": "Die Antworten überprüfen. Die Auswahlen werden als richtig, falsch oder fehlend markiert.",
                    "a11yShowSolution": "Die Lösung anzeigen. Die richtigen Lösungen werden in der Aufgabe angezeigt.",
                    "a11yRetry": "Die Aufgabe wiederholen. Alle Versuche werden zurückgesetzt und die Aufgabe wird erneut gestartet."
                },
                "confirmCheck": {
                    "header": "Beenden?",
                    "body": "Ganz sicher beenden?",
                    "cancelLabel": "Abbrechen",
                    "confirmLabel": "Beenden"
                },
                "confirmRetry": {
                    "header": "Wiederholen?",
                    "body": "Ganz sicher wiederholen?",
                    "cancelLabel": "Abbrechen",
                    "confirmLabel": "Bestätigen"
                }
            },
            "subContentId": generate_uuid(),
            "metadata": {
                "contentType": "Multiple Choice",
                "license": "U",
                "title": "Multiple Choice",
                "authors": [],
                "changes": [],
                "extraTitle": "Multiple Choice"
            }
        }

        options = question.get("options", [])
        if not isinstance(options, list):
            st.warning(f"'options' is not a list in MultipleChoice question: {question.get('question', 'Keine Frage')}")
            return h5p_question

        for option in options:
            answer = {
                "text": option.get("text", ""),
                "correct": option.get("is_correct", False),
                "tipsAndFeedback": {
                    "tip": "",
                    "chosenFeedback": f"<div>{option.get('feedback', '')}</div>\n",
                    "notChosenFeedback": ""
                }
            }
            h5p_question["params"]["answers"].append(answer)

        return h5p_question

    except Exception as e:
        st.error(f"Error mapping MultipleChoice question: {e}")
        return {}

# Function to map TrueFalse questions to H5P format
def map_true_false(question):
    try:
        correct_answer = question.get("correct_answer", False)
        feedback_correct = question.get("feedback_correct", "")
        feedback_incorrect = question.get("feedback_incorrect", "")

        h5p_question = {
            "library": "H5P.TrueFalse 1.8",
            "params": {
                "question": question.get("question", "Keine Frage gestellt."),
                "correct": "true" if correct_answer else "false",
                "behaviour": {
                    "enableRetry": False,
                    "enableSolutionsButton": False,
                    "enableCheckButton": True,
                    "confirmCheckDialog": False,
                    "confirmRetryDialog": False,
                    "autoCheck": False,
                    "feedbackOnCorrect": feedback_correct,
                    "feedbackOnWrong": feedback_incorrect
                },
                "media": {
                    "disableImageZooming": False
                },
                "l10n": {
                    "trueText": "Wahr",
                    "falseText": "Falsch",
                    "score": "Du hast @score von @total Punkten erreicht.",
                    "checkAnswer": "Überprüfen",
                    "submitAnswer": "Absenden",
                    "showSolutionButton": "Lösung anzeigen",
                    "tryAgain": "Wiederholen",
                    "wrongAnswerMessage": "Falsche Antwort",
                    "correctAnswerMessage": "Richtige Antwort",
                    "scoreBarLabel": "Du hast :num von :total Punkten erreicht.",
                    "a11yCheck": "Die Antworten überprüfen. Die Antwort wird als richtig, falsch oder unbeantwortet markiert.",
                    "a11yShowSolution": "Die Lösung anzeigen. Die richtige Lösung wird in der Aufgabe angezeigt.",
                    "a11yRetry": "Die Aufgabe wiederholen. Alle Versuche werden zurückgesetzt, und die Aufgabe wird erneut gestartet."
                },
                "confirmCheck": {
                    "header": "Beenden?",
                    "body": "Ganz sicher beenden?",
                    "cancelLabel": "Abbrechen",
                    "confirmLabel": "Beenden"
                },
                "confirmRetry": {
                    "header": "Wiederholen?",
                    "body": "Ganz sicher wiederholen?",
                    "cancelLabel": "Abbrechen",
                    "confirmLabel": "Bestätigen"
                }
            },
            "subContentId": generate_uuid(),
            "metadata": {
                "contentType": "True/False Question",
                "license": "U",
                "title": "Richtig Falsch",
                "authors": [],
                "changes": [],
                "extraTitle": "Richtig Falsch"
            }
        }

        return h5p_question

    except Exception as e:
        st.error(f"Error mapping TrueFalse question: {e}")
        return {}

# Function to map questions to H5P format
def map_questions_to_h5p(llm_questions, source_name):
    h5p_questions = []
    for idx, question in enumerate(llm_questions, start=1):
        q_type = question.get("type", "").strip()
        if q_type == "MultipleChoice":
            h5p_q = map_multiple_choice(question)
        elif q_type == "TrueFalse":
            h5p_q = map_true_false(question)
        else:
            st.warning(f"Unsupported question type '{q_type}' in '{source_name}'. Skipping question #{idx}.")
            continue  # Skip unsupported question types
        if h5p_q:  # Only append if mapping was successful
            h5p_questions.append(h5p_q)
    st.info(f"Mapped {len(h5p_questions)} questions from '{source_name}'.")
    return h5p_questions

# Function to create H5P content structure with customization
def create_h5p_content(questions, title, randomization, pool_size, pass_percentage):
    h5p_content = {
        "introPage": {
            "showIntroPage": True,
            "startButtonText": "Quiz starten",
            "title": title,
            "introduction": (
                "<p style=\"text-align:center\"><strong>Starten Sie das Quiz, um Ihr Wissen zu testen.</strong></p>"
                "<p style=\"text-align:center\"> </p>"
                f"<p style=\"text-align:center\"> <strong>Pro Runde werden zufällig {pool_size} Fragen angezeigt.</strong></p>"
                "<p style=\"text-align:center\"><strong>Wiederholen Sie die Übung, um weitere Fragen zu beantworten.</strong></p>"
            ),
            "backgroundImage": {
                "path": "images/file-_jmSDW4b9EawjImv.png",
                "mime": "image/png",
                "copyright": {
                    "license": "U"
                },
                "width": 52,
                "height": 52
            }
        },
        "progressType": "textual",
        "passPercentage": pass_percentage,
        "disableBackwardsNavigation": True,
        "randomQuestions": randomization,
        "endGame": {
            "showResultPage": True,
            "showSolutionButton": True,
            "showRetryButton": True,
            "noResultMessage": "Quiz beendet",
            "message": "Dein Ergebnis:",
            "scoreBarLabel": "Du hast @score von @total Punkten erreicht.",
            "overallFeedback": [
                {
                    "from": 0,
                    "to": 50,
                    "feedback": "Kein Grund zur Sorge! Tipp: Schau dir die Lösungen an, bevor du in die nächste Runde startest."
                },
                {
                    "from": 51,
                    "to": 75,
                    "feedback": "Du weisst schon einiges über das Thema. Mit jeder Wiederholung kannst du dich steigern."
                },
                {
                    "from": 76,
                    "to": 100,
                    "feedback": "Gut gemacht!"
                }
            ],
            "solutionButtonText": "Lösung anzeigen",
            "retryButtonText": "Nächste Runde",
            "finishButtonText": "Beenden",
            "submitButtonText": "Absenden",
            "showAnimations": False,
            "skippable": False,
            "skipButtonText": "Video überspringen"
        },
        "override": {
            "checkButton": True
        },
        "texts": {
            "prevButton": "Zurück",
            "nextButton": "Weiter",
            "finishButton": "Beenden",
            "submitButton": "Absenden",
            "textualProgress": "Frage @current von @total",
            "jumpToQuestion": "Frage %d von %total",
            "questionLabel": "Frage",
            "readSpeakerProgress": "Frage @current von @total",
            "unansweredText": "Unbeantwortet",
            "answeredText": "Beantwortet",
            "currentQuestionText": "Aktuelle Frage",
            "navigationLabel": "Fragen"
        },
        "poolSize": pool_size,
        "questions": questions
    }
    return h5p_content

# Function to clean JSON content by replacing 'ß' with 'ss'
def clean_json_content(content_str):
    try:
        cleaned_content = content_str.replace('ß', 'ss')
        # Validate JSON
        json.loads(cleaned_content)
        return cleaned_content
    except json.JSONDecodeError as e:
        st.error(f"JSON decoding error after cleaning: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error during JSON cleaning: {e}")
        return None

# Function to create H5P package in memory
def create_h5p_package(content_json_str, template_zip_path, title, user_image_bytes=None):
    try:
        # Load the template zip file
        with open(template_zip_path, 'rb') as f:
            template_bytes = f.read()

        with zipfile.ZipFile(io.BytesIO(template_bytes), 'r') as template_zip:
            # Create a new in-memory zip file
            in_memory_zip = io.BytesIO()
            with zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                # Copy all contents from the template zip to the new zip
                for item in template_zip.infolist():
                    file_data = template_zip.read(item.filename)
                    new_zip.writestr(item, file_data)

                # Add the cleaned content.json to the 'content/' folder
                new_zip.writestr('content/content.json', content_json_str.encode('utf-8'))

                # **Begin Image Replacement**
                if user_image_bytes:
                    # Define the path to the image in the H5P package
                    image_path = 'content/images/file-_jmSDW4b9EawjImv.png'
                    new_zip.writestr(image_path, user_image_bytes)
                    st.info("Uploaded image has been successfully integrated into the H5P package.")
                # **End Image Replacement**

                # Create h5p.json with dynamic titles
                h5p_content = {
                    "embedTypes": ["iframe"],
                    "language": "en",
                    "license": "U",
                    "extraTitle": title,  # Dynamic title
                    "title": title,        # Dynamic title
                    "mainLibrary": "H5P.QuestionSet",
                    "preloadedDependencies": [
                        {"machineName": "H5P.MultiChoice", "majorVersion": 1, "minorVersion": 16},
                        {"machineName": "FontAwesome", "majorVersion": 4, "minorVersion": 5},
                        {"machineName": "H5P.JoubelUI", "majorVersion": 1, "minorVersion": 3},
                        {"machineName": "H5P.Transition", "majorVersion": 1, "minorVersion": 0},
                        {"machineName": "H5P.FontIcons", "majorVersion": 1, "minorVersion": 0},
                        {"machineName": "H5P.Question", "majorVersion": 1, "minorVersion": 5},
                        {"machineName": "H5P.TrueFalse", "majorVersion": 1, "minorVersion": 8},
                        {"machineName": "H5P.Video", "majorVersion": 1, "minorVersion": 6},
                        {"machineName": "H5P.QuestionSet", "majorVersion": 1, "minorVersion": 20}
                    ],
                    "defaultLanguage": "de"
                }

                h5p_json_str = json.dumps(h5p_content, indent=4)
                # Add h5p.json to the root of the zip
                new_zip.writestr('h5p.json', h5p_json_str.encode('utf-8'))

        in_memory_zip.seek(0)
        return in_memory_zip.getvalue()

    except FileNotFoundError:
        st.error(f"Template zip file not found at '{template_zip_path}'. Please ensure the path is correct.")
        return None
    except Exception as e:
        st.error(f"Error creating H5P package: {e}")
        return None

# Function to process each JSON input (from file or text)
def process_json_input(json_data, source_name, template_zip_path, title, randomization, pool_size, pass_percentage, user_image_bytes=None):
    try:
        if not isinstance(json_data, dict):
            st.error(f"Expected a JSON object, but got {type(json_data).__name__}.")
            return None

        questions = json_data.get("questions", [])
        if not isinstance(questions, list):
            st.error(f"Expected 'questions' to be a list in '{source_name}', but got {type(questions).__name__}.")
            return None

        if not questions:
            st.warning(f"No questions found in '{source_name}'.")
            return None

        # Map questions to H5P format
        h5p_questions = map_questions_to_h5p(questions, source_name)
        if not h5p_questions:
            st.warning(f"No valid questions mapped from '{source_name}'.")
            return None

        # Create H5P content structure with customization
        h5p_content = create_h5p_content(h5p_questions, title, randomization, pool_size, pass_percentage)

        # Serialize to JSON string
        h5p_content_str = json.dumps(h5p_content, ensure_ascii=False, indent=4)

        # Clean the JSON content by replacing 'ß' with 'ss'
        cleaned_content = clean_json_content(h5p_content_str)
        if not cleaned_content:
            st.error(f"Cleaning JSON content failed for '{source_name}'.")
            return None

        # Generate a title based on the source name if not provided
        base_name = Path(title).stem if isinstance(title, str) else "H5P_Content"

        # Create H5P package with the user-uploaded image
        h5p_package_bytes = create_h5p_package(cleaned_content, template_zip_path, base_name, user_image_bytes=user_image_bytes)
        if not h5p_package_bytes:
            st.error(f"Failed to create H5P package for '{source_name}'.")
            return None

        return h5p_package_bytes

    except json.JSONDecodeError as e:
        st.error(f"JSONDecodeError while loading '{source_name}': {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error while processing '{source_name}': {e}")
        return None

# Streamlit App Layout
def main():
    st.title("LLM JSON to H5P Converter")
    st.write("""
        Transform your LLM-generated JSON files into H5P `.h5p` packages seamlessly with customizable options.
    """)

    # Sidebar for instructions or additional options
    with st.sidebar.expander("Instructions", expanded=False):
        st.info("""
            **Paste JSON:**
            1. **Paste JSON Content:** Use the text area to paste your JSON data directly.
                Use [customGPT H5P MF & TF](https://chatgpt.com/g/g-67738981e5e081919b6fc8e93e287453-h5p-mf-tf) to generate the JSON format.
            2. **Process JSON:** Click the "Create H5P Package" button to transform the pasted JSON.
            3. **Download H5P File:** After processing, download your `.h5p` package.

            **Customization Options:**
            1. **Title of the Unit:** Enter a custom title for your H5P content.
            2. **Randomization of Questions:** Toggle to enable or disable random question order.
            3. **Limit Questions:** Select the number of questions to display per session.
            4. **Percentage to Succeed:** Choose the passing score percentage.

            **Image Upload:**
            1. **Upload Title Image:** Upload an image to be used as the title image for your H5P content.
            2. **Note:** The uploaded image will replace the default image in the H5P package.
        """)

    # Customization Options
    st.sidebar.header("Customization Options")

    # Title of the Unit
    title = st.sidebar.text_input("Title of the Unit", value="Generated Quiz")

    # Randomization of Questions
    randomization = st.sidebar.checkbox("Randomize Questions", value=True)

    # Limit Questions
    pool_size = st.sidebar.slider("Number of Questions to Show", min_value=1, max_value=16, value=7)

    # Percentage to Succeed
    pass_percentage = st.sidebar.selectbox(
        "Percentage to Succeed",
        options=[50, 60, 66, 75, 100],
        index=1  # Default to 60%
    )

    # **Begin Image Upload Feature**
    st.sidebar.header("Upload Title Image")
    uploaded_image = st.sidebar.file_uploader("Choose an image for the title", type=["png", "jpg", "jpeg"])
    user_image_bytes = None
    if uploaded_image:
        try:
            user_image_bytes = uploaded_image.read()
            st.sidebar.success("Image uploaded successfully!")
        except Exception as e:
            st.sidebar.error(f"Error reading the uploaded image: {e}")
    # **End Image Upload Feature**

    # JSON Text Area
    st.header("Paste JSON Content created with [customGPT H5P MF & TF](https://chatgpt.com/g/g-67738981e5e081919b6fc8e93e287453-h5p-mf-tf) below")
    pasted_json = st.text_area("Paste your JSON here:", height=300)

    # Path to the template zip
    template_zip_path = Path(__file__).parent / "templates" / "MC_TF.zip"

    # Check if the template exists
    if not template_zip_path.exists():
        st.error(f"Template zip file not found at '{template_zip_path}'. Please ensure the 'MC_TF.zip' is in the 'templates' folder.")
        return

    # Process pasted JSON
    if pasted_json.strip():
        st.subheader("Processing Pasted JSON")
        if st.button("Create H5P Package"):
            try:
                json_data = json.loads(pasted_json)
                h5p_package = process_json_input(
                    json_data=json_data,
                    source_name="Pasted_JSON",
                    template_zip_path=template_zip_path,
                    title=title,
                    randomization=randomization,
                    pool_size=pool_size,
                    pass_percentage=pass_percentage,
                    user_image_bytes=user_image_bytes  # Pass the uploaded image bytes
                )
                if h5p_package:
                    h5p_filename = "pasted_content.h5p"
                    st.download_button(
                        label=f"Download `{h5p_filename}`",
                        data=h5p_package,
                        file_name=h5p_filename,
                        mime="application/zip"
                    )
            except json.JSONDecodeError as e:
                st.error(f"JSONDecodeError in pasted content: {e}")
            except Exception as e:
                st.error(f"Error processing pasted JSON: {e}")

    if not pasted_json.strip():
        st.info("Please upload a JSON file or paste JSON content above to begin.")

if __name__ == "__main__":
    main()
