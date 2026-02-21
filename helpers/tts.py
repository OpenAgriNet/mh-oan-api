import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

def text_to_speech_bhashini(text, source_lang='mr', gender='female', sampling_rate=8000):
    url = 'https://dhruva-api.bhashini.gov.in/services/inference/pipeline'
    headers = {
        'Accept': '*/*',
        'Authorization': os.getenv('MEITY_API_KEY_VALUE'),
        'Content-Type': 'application/json',
    }
    data = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": source_lang
                    },
                    "serviceId": "",  
                    "gender": gender,
                    "samplingRate": sampling_rate
                }
            }
        ],
        "inputData": {
            "input": [
                {
                    "source": text
                }
            ]
        }
    }
    response = requests.post(url, headers=headers, json=data)
    assert response.status_code == 200, f"Error: {response.status_code} {response.text}"
    response_json = response.json()

    audio_content = response_json['pipelineResponse'][0]['audio'][0]['audioContent']
    audio_data = base64.b64decode(audio_content)
    return audio_data

def text_to_speech_bhili(
    text,
    target_lang,
    gender='female',
    sampling_rate=8000
):
    url = 'https://dhruva-api.bhashini.gov.in/services/inference/tts/voice-cloning'
    
    headers = {
        'Accept': '*/*',
        'Authorization': os.getenv('MEITY_API_KEY_VALUE'),  # Don't hardcode tokens. Ever.
        'Content-Type': 'application/json',
    }

    data = {
        "config": {
            "language": {
                "sourceLanguage": target_lang
            },
            "serviceId": "bhashini/ai4b/bhili-tts",
            "gender": gender,
            "samplingRate": sampling_rate
        },
        "input": [
            {
                "source": text,
                "refText": "माहारी पाकवुला ई बिमारी की वाचवुला यंत्रणा हाय, तिया की पीक सुरक्षित रेहे",
                "refAudioUrl": "https://bhashinimigrationns.sosnm1.shakticloud.ai:9024/logsdata/ref_audio.wav"
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    assert response.status_code == 200, f"Error: {response.status_code} {response.text}"
    
    response_json = response.json()

    audio_content = response_json['audio'][0]['audioContent']
    audio_data = base64.b64decode(audio_content)

    return audio_data