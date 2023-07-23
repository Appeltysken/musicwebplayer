document.addEventListener("DOMContentLoaded", () => {
	const searchInput = document.getElementById("search-input");
	const searchButton = document.getElementById("search-button");
	const searchResults = document.getElementById("search-results");
	const audioPlayer = document.getElementById("audio-player");
	const prevButton = document.getElementById("prev-button");
	const playButton = document.getElementById("play-button");
	const nextButton = document.getElementById("next-button");
	const volumeSlider = document.getElementById("volume-slider");
	const currentTimeElement = document.getElementById("current-time");
	const durationElement = document.getElementById("duration");
	const timeSlider = document.getElementById("time-slider");

	let currentTrackIndex = 0;
	let tracks = [];

	document.addEventListener("click", (event) => {
		if (event.target.id === "search-button") {
			handleSearch();
		} else if (event.target.id === "prev-button") {
			handlePrev();
		} else if (event.target.id === "play-button") {
			handlePlay();
		} else if (event.target.id === "next-button") {
			handleNext();
		}
	});

	window.addEventListener("beforeunload", () => {
		const state = {
			currentTrackIndex,
			tracks,
			currentTime: audioPlayer.currentTime,
			isPlaying: !audioPlayer.paused,
		};
		localStorage.setItem("musicPlayerState", JSON.stringify(state));
	});

	async function handleSearch() {
		const searchTerm = searchInput.value.toLowerCase();
		try {
			const response = await fetch(
				`https://api.jamendo.com/v3.0/tracks/?client_id=4cb570af&format=json&limit=10&search=${searchTerm}&order=relevance`,
			);
			const { results } = await response.json();

			tracks = results.filter((track) => {
				const trackName = track.name.toLowerCase();
				const artistName = track.artist_name.toLowerCase();
				return trackName.includes(searchTerm) || artistName.includes(searchTerm);
			});

			if (tracks.length === 0) {
				searchResults.innerHTML = "<li>Нет результатов</li>";
			} else {
				currentTrackIndex = 0;
				displayTrack(tracks[currentTrackIndex]);
				updateAudioSource(tracks[currentTrackIndex].audio);
				updateTrackInfo(tracks[currentTrackIndex]);
			}
		} catch (error) {
			console.error("Ошибка поиска трека:", error);
		}
	}

	function displayTrack(track) {
		searchResults.innerHTML = `<li>${track.name} - ${track.artist_name}</li>`;
	}

	function updateAudioSource(audioUrl) {
		audioPlayer.src = audioUrl;
		audioPlayer.load();
	}

	function updateTrackInfo(track) {
		const trackNameElement = document.getElementById("track-name");
		const artistNameElement = document.getElementById("artist-name");
		const trackImageElement = document.getElementById("track-image");

		trackNameElement.textContent = track.name;
		artistNameElement.textContent = track.artist_name;
		trackImageElement.src = track.image;
	}

	searchInput.addEventListener("input", () => {
		setTimeout(handleSearch, 300);
	});

	function handlePrev() {
		if (tracks.length === 0) return;
		currentTrackIndex = (currentTrackIndex - 1 + tracks.length) % tracks.length;
		displayTrack(tracks[currentTrackIndex]);
		updateAudioSource(tracks[currentTrackIndex].audio);
		updateTrackInfo(tracks[currentTrackIndex]);

		if (!audioPlayer.paused) {
			audioPlayer.pause();
			playButton.innerHTML = '<button id="play-button" class="player-controls"><i class="fas fa-play"></i></button>';
		}
	}

	function handlePlay() {
		if (tracks.length === 0) return;

		if (audioPlayer.paused) {
			audioPlayer.play();
			playButton.innerHTML = '<button id="play-button" class="player-controls"><i class="fas fa-pause"></i></button>';
		} else {
			audioPlayer.pause();
			playButton.innerHTML = '<button id="play-button" class="player-controls"><i class="fas fa-play"></i></button>';
		}
	}

	function handleNext() {
		if (tracks.length === 0) return;
		const wasPaused = audioPlayer.paused;
		currentTrackIndex = (currentTrackIndex + 1) % tracks.length;
		displayTrack(tracks[currentTrackIndex]);
		updateAudioSource(tracks[currentTrackIndex].audio);
		updateTrackInfo(tracks[currentTrackIndex]);

		if (!wasPaused) {
			audioPlayer.play();
			playButton.innerHTML = '<button id="play-button" class="player-controls"><i class="fas fa-pause"></i></button>';
		}
	}

	volumeSlider.addEventListener("input", () => {
		audioPlayer.volume = volumeSlider.value;
	});

	audioPlayer.addEventListener("ended", () => {
		handleNext();
	});

	audioPlayer.addEventListener("loadedmetadata", () => {
		const duration = audioPlayer.duration;
		durationElement.textContent = formatTime(duration);
		timeSlider.max = duration;
	});

	audioPlayer.addEventListener("timeupdate", () => {
		const currentTime = audioPlayer.currentTime;
		currentTimeElement.textContent = formatTime(currentTime);
		timeSlider.value = currentTime;
	});

	timeSlider.addEventListener("input", () => {
		const seekTime = parseFloat(timeSlider.value);
		audioPlayer.currentTime = seekTime;
	});

	function formatTime(time) {
		const minutes = Math.floor(time / 60);
		const seconds = Math.floor(time % 60);
		return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
	}
});
