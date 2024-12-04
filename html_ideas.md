html ???????
```html
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aplikacja Rozpoznawania Mowy</title>
    <link rel="stylesheet" href="https://pyscript.net/latest/pyscript.css" />
    <script defer src="https://pyscript.net/latest/pyscript.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        #audioPlayer {
            margin-bottom: 20px;
        }
        #results {
            margin-top: 20px;
        }
        .segment {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <h1>Aplikacja Rozpoznawania Mowy</h1>
    <audio id="audioPlayer" controls></audio>
    <button id="startButton">Rozpocznij</button>
    <button id="repeatButton" disabled>Powtórz Segment</button>
    <div id="results"></div>

    <py-script>
        import asyncio
        from pyodide.http import pyfetch
        from js import document, AudioContext, MediaRecorder, Blob, FormData, alert, prompt

        audio_url = "path_to_your_audio_file.wav"  # Replace with your audio file path
        audio_player = Element("audioPlayer")
        start_button = Element("startButton")
        repeat_button = Element("repeatButton")
        results_div = Element("results")

        audio_context = None
        source_node = None
        script_processor_node = None
        current_segment = 0
        segments = []
        results = []

        async def init():
            audio_player.src = audio_url

        async def load_model():
            # Load your LLM model here if needed
            pass

        async def start_processing():
            global audio_context, source_node, script_processor_node
            if not audio_context:
                audio_context = AudioContext.new()
            source_node = audio_context.createMediaElementSource(audio_player)
            script_processor_node = audio_context.createScriptProcessor(4096, 1, 1)

            source_node.connect(script_processor_node)
            script_processor_node.connect(audio_context.destination)

            script_processor_node.onaudioprocess = lambda audio_processing_event: None

            audio_player.play()
            await process_audio()

        async def repeat_segment():
            await process_audio()

        async def process_audio():
            duration = 5  # Duration of each segment in seconds
            start_time = current_segment * duration
            end_time = start_time + duration

            audio_player.currentTime = start_time
            audio_player.play()

            recorded_chunks = []
            media_recorder = MediaRecorder.new(audio_context.createMediaStreamDestination().stream)

            def on_data_available(event):
                recorded_chunks.append(event.data)

            def on_stop():
                audio_blob = Blob.new(recorded_chunks, {'type': 'audio/wav'})
                form_data = FormData.new()
                form_data.append('audio', audio_blob, 'segment.wav')

                async def fetch_process_audio():
                    response = await pyfetch(url="/process-audio", method="POST", body=form_data)
                    recognized_words = await response.json()
                    user_words = prompt(f"Powtórz słowa: {', '.join(recognized_words)}").split(", ")
                    user_words = [word.strip() for word in user_words]

                    segment_result = {
                        "segmentNumber": current_segment + 1,
                        "recognizedWords": recognized_words,
                        "userWords": user_words,
                        "correctWords": [],
                        "incorrectWords": []
                    }

                    for i in range(len(recognized_words)):
                        if recognized_words[i] == user_words[i]:
                            segment_result["correctWords"].append(recognized_words[i])
                        else:
                            segment_result["incorrectWords"].append({
                                "recognized": recognized_words[i],
                                "said": user_words[i]
                            })

                    results.append(segment_result)
                    display_results()

                    nonlocal current_segment
                    current_segment += 1
                    if audio_player.currentTime < audio_player.duration:
                        repeat_button.disabled = False
                    else:
                        alert("Koniec nagrania.")

                asyncio.ensure_future(fetch_process_audio())

            media_recorder.ondataavailable = on_data_available
            media_recorder.onstop = on_stop

            media_recorder.start()
            audio_context.resume()
            await asyncio.sleep(duration)
            media_recorder.stop()
            audio_player.pause()

        def display_results():
            results_div.element.innerHTML = ""
            for result in results:
                segment_div = document.createElement("div")
                segment_div.className = "segment"
                segment_div.innerHTML = f"""
                    <strong>Segment {result['segmentNumber']}:</strong><br>
                    Rozpoznane słowa: {', '.join(result['recognizedWords'])}<br>
                    Twoje słowa: {', '.join(result['userWords'])}<br>
                    Poprawne słowa: {', '.join(result['correctWords'])}<br>
                    Błędne słowa: {', '.join([f"{w['recognized']} (powiedziałeś: {w['said']})" for w in result['incorrectWords']])}
                """
                results_div.element.appendChild(segment_div)

        start_button.element.onclick = start_processing
        repeat_button.element.onclick = repeat_segment

        asyncio.ensure_future(init())
    </py-script>
</body>
</html>
```
Backend (Java with Spring Boot)

The backend will handle receiving audio segments, processing them with an LLM, and returning the recognized words.

    Add the necessary dependencies in pom.xml:

xml

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>

    Create a controller to handle audio processing (AudioController.java):

java

package com.example.audioapp;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;

@RestController
public class AudioController {

    @PostMapping("/process-audio")
    public List<String> processAudio(@RequestParam("audio") MultipartFile audioFile) throws IOException {
        // Save the uploaded file to a temporary location
        String tempDir = System.getProperty("java.io.tmpdir");
        Path tempFilePath = Paths.get(tempDir, "segment.wav");
        Files.write(tempFilePath, audioFile.getBytes());

        // Process the audio file using your LLM model
        // For demonstration purposes, we'll return a static list of words
        List<String> recognizedWords = Arrays.asList("word1", "word2", "word3", "word4", "word5");

        // Delete the temporary file
        Files.delete(tempFilePath);

        return recognizedWords;
    }
}

    Create the main application class (AudioAppApplication.java):

```java
package com.example.audioapp;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class AudioAppApplication {

    public static void main(String[] args) {
        SpringApplication.run(AudioAppApplication.class, args);
    }
}
```
Running the Application

    Frontend: Place the index.html file in the src/main/resources/static directory of your Spring Boot project.
    Backend: Run the Spring Boot application. Ensure it's accessible at http://localhost:8080.
    Access the Application: Open http://localhost:8080/index.html in a web browser.

Replace 'path_to_your_audio_file.wav' with the actual path to your audio file. The frontend will send audio segments to the backend for processing, and the backend will return the recognized words. The frontend will then prompt the user to repeat the words and display the results.
Final Directory Structure

Your final directory structure should look something like this:

code
```
UwuBis-soundhelper/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/
│   │   │       └── example/
│   │   │           └── audioapp/
│   │   │               ├── AudioAppApplication.java
│   │   │               └── AudioController.java
│   │   └── resources/
│   │       └── static/
│   │           └── index.html
├── pom.xml
```
