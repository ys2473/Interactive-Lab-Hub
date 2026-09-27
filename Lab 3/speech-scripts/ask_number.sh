SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../.venv/bin/activate"
cd "$SCRIPT_DIR"

python3 -m piper -m en_US-lessac-medium -f number_question.wav -- "Hello Yan. What is your phone number?"
aplay number_question.wav
echo "Recording your answer for 7 seconds..."
arecord -d 7 -f S16_LE -c 1 -r 16000 number_answer.wav
echo "Transcribing..."
python transcribe.py number_answer.wav --model base.en
