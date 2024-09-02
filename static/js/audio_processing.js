let audioElement, progressBar, currentTimeSpan, durationSpan;

function base64ToArrayBuffer(base64) {
    var binary_string = window.atob(base64);
    var len = binary_string.length;
    var bytes = new Uint8Array(len);
    for (var i = 0; i < len; i++) {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}

async function processAndPlayAudio() {
    console.log("Processing and playing audio...");
    
    try {
        var audioData = document.getElementById('audio-data');
        var audio1Base64 = audioData.dataset.audio1;
        var audio2Base64 = audioData.dataset.audio2;
        var bgMusicBase64 = audioData.dataset.audio3;
        
        if (!audio1Base64 || !audio2Base64 || !bgMusicBase64) {
            throw new Error("One or more audio data strings are missing");
        }
        
        var audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        const [audio1, audio2, bgMusic] = await Promise.all([
            audioContext.decodeAudioData(base64ToArrayBuffer(audio1Base64)),
            audioContext.decodeAudioData(base64ToArrayBuffer(audio2Base64)),
            audioContext.decodeAudioData(base64ToArrayBuffer(bgMusicBase64))
        ]);
        
        console.log("Audio buffers decoded successfully");

        const targetSampleRate = audio1.sampleRate;
        const normalizedAudio2 = await resampleBuffer(audioContext, audio2, targetSampleRate);
        const normalizedBgMusic = await resampleBuffer(audioContext, bgMusic, targetSampleRate);
        
        const trimmedBgMusic = trimAudio(audioContext, normalizedBgMusic, normalizedAudio2.duration);
        
        const mixedAudio2 = await mixAudio(audioContext, normalizedAudio2, trimmedBgMusic, 0.8, 0.2);
        
        const finalAudio = await concatenateAudio(audioContext, audio1, mixedAudio2);
        
        const wav = bufferToWave(finalAudio, finalAudio.length);
        const blob = new Blob([wav], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);

        setupAudioPlayer(url);
        createDownloadLink(finalAudio);
    } catch (error) {
        console.error("Error processing audio:", error);
    }
}

function trimAudio(context, buffer, duration) {
    var trimmedBuffer = context.createBuffer(
        buffer.numberOfChannels,
        Math.min(buffer.length, Math.floor(duration * buffer.sampleRate)),
        buffer.sampleRate
    );

    for (var channel = 0; channel < buffer.numberOfChannels; channel++) {
        trimmedBuffer.copyToChannel(buffer.getChannelData(channel).slice(0, trimmedBuffer.length), channel);
    }

    return trimmedBuffer;
}

function mixAudio(context, buffer1, buffer2, volume1, volume2) {
    var numberOfChannels = Math.max(buffer1.numberOfChannels, buffer2.numberOfChannels);
    var mixedBuffer = context.createBuffer(
        numberOfChannels,
        Math.max(buffer1.length, buffer2.length),
        buffer1.sampleRate
    );

    for (var channel = 0; channel < numberOfChannels; channel++) {
        var outputData = mixedBuffer.getChannelData(channel);
        var b1Data = buffer1.getChannelData(Math.min(channel, buffer1.numberOfChannels - 1));
        var b2Data = buffer2.getChannelData(Math.min(channel, buffer2.numberOfChannels - 1));

        for (var i = 0; i < outputData.length; i++) {
            outputData[i] = (i < b1Data.length ? b1Data[i] * volume1 : 0) + (i < b2Data.length ? b2Data[i] * volume2 : 0);
        }
    }

    return mixedBuffer;
}

function concatenateAudio(context, buffer1, buffer2) {
    var numberOfChannels = Math.max(buffer1.numberOfChannels, buffer2.numberOfChannels);
    var finalBuffer = context.createBuffer(
        numberOfChannels,
        buffer1.length + buffer2.length,
        buffer1.sampleRate
    );

    for (var channel = 0; channel < numberOfChannels; channel++) {
        var outputData = finalBuffer.getChannelData(channel);
        var b1Data = buffer1.getChannelData(Math.min(channel, buffer1.numberOfChannels - 1));
        var b2Data = buffer2.getChannelData(Math.min(channel, buffer2.numberOfChannels - 1));

        outputData.set(b1Data, 0);
        outputData.set(b2Data, buffer1.length);
    }

    return finalBuffer;
}

function bufferToWave(abuffer, len) {
    var numOfChan = abuffer.numberOfChannels,
        length = len * numOfChan * 2 + 44,
        buffer = new ArrayBuffer(length),
        view = new DataView(buffer),
        channels = [], i, sample,
        offset = 0,
        pos = 0;

    setUint32(0x46464952);
    setUint32(length - 8);
    setUint32(0x45564157);
    setUint32(0x20746d66);
    setUint32(16);
    setUint16(1);
    setUint16(numOfChan);
    setUint32(abuffer.sampleRate);
    setUint32(abuffer.sampleRate * 2 * numOfChan);
    setUint16(numOfChan * 2);
    setUint16(16);
    setUint32(0x61746164);
    setUint32(len * numOfChan * 2);

    for(i = 0; i < abuffer.numberOfChannels; i++)
        channels.push(abuffer.getChannelData(i));

    while(pos < len) {
        for(i = 0; i < numOfChan; i++) {
            sample = Math.max(-1, Math.min(1, channels[i][pos]));
            view.setInt16(44 + offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
            offset += 2;
        }
        pos++;
    }

    return buffer;

    function setUint16(data) {
        view.setUint16(pos, data, true);
        pos += 2;
    }

    function setUint32(data) {
        view.setUint32(pos, data, true);
        pos += 4;
    }
}
async function resampleBuffer(audioContext, buffer, targetSampleRate) {
    if (buffer.sampleRate === targetSampleRate) {
        return buffer;
    }
    
    const offlineCtx = new OfflineAudioContext(
        buffer.numberOfChannels,
        buffer.duration * targetSampleRate,
        targetSampleRate
    );
    
    const source = offlineCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(offlineCtx.destination);
    source.start(0);
    
    return offlineCtx.startRendering();
}

function setupAudioPlayer(audioUrl) {
    const audioPlayer = document.getElementById('audio-player');
    audioElement = document.getElementById('audio-element');
    progressBar = document.getElementById('progress-bar');
    currentTimeSpan = document.getElementById('current-time');
    durationSpan = document.getElementById('duration');

    audioElement.src = audioUrl;
    audioPlayer.style.display = 'block';

    audioElement.addEventListener('loadedmetadata', () => {
        progressBar.max = audioElement.duration;
        updateDurationDisplay();
    });

    audioElement.addEventListener('timeupdate', updateProgressBar);
    progressBar.addEventListener('input', seek);
}

function updateProgressBar() {
    progressBar.value = audioElement.currentTime;
    updateCurrentTimeDisplay();
}

function seek() {
    audioElement.currentTime = progressBar.value;
}

function updateCurrentTimeDisplay() {
    currentTimeSpan.textContent = formatTime(audioElement.currentTime);
}

function updateDurationDisplay() {
    durationSpan.textContent = formatTime(audioElement.duration);
}

function formatTime(time) {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function createDownloadLink(audioBuffer) {
    const wav = bufferToWave(audioBuffer, audioBuffer.length);
    const blob = new Blob([wav], { type: 'audio/wav' });
    const url = URL.createObjectURL(blob);
    const downloadLink = document.createElement("a");
    downloadLink.href = url;
    downloadLink.download = "final_audio.wav";
    downloadLink.innerHTML = "Download Final Audio";
    document.getElementById('audio-player').appendChild(downloadLink);
}

document.addEventListener('DOMContentLoaded', function() {
    var button = document.getElementById('process-audio-btn');
    if(button) {
        button.addEventListener('click', processAndPlayAudio);
    } else {
        console.error("Button not found");
    }
});

processAndPlayAudio();