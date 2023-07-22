document.addEventListener("DOMContentLoaded", () => {
	const searchInput = document.getElementById("search-input");
	const searchButton = document.getElementById("search-button");
	const searchResults = document.getElementById("search-results");
	const audioPlayer = document.getElementById("audio-player");
	const prevButton = document.getElementById("prev-button");
	const playButton = document.getElementById("play-button");
	const nextButton = document.getElementById("next-button");
	const volumeSlider = document.getElementById("volume-slider");

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

	function handlePrev() {
		if (tracks.length === 0) return;
		currentTrackIndex = (currentTrackIndex - 1 + tracks.length) % tracks.length;
		displayTrack(tracks[currentTrackIndex]);
		updateAudioSource(tracks[currentTrackIndex].audio);
		audioPlayer.play();
	}

	function handlePlay() {
		if (tracks.length === 0) return;

		if (audioPlayer.paused) {
			audioPlayer.play();
			playButton.innerHTML = '<i class="fas fa-pause"></i>';
		} else {
			audioPlayer.pause();
			playButton.innerHTML = '<i class="fas fa-play"></i>';
		}
	}

	function handleNext() {
		if (tracks.length === 0) return;
		currentTrackIndex = (currentTrackIndex + 1) % tracks.length;
		displayTrack(tracks[currentTrackIndex]);
		updateAudioSource(tracks[currentTrackIndex].audio);
		audioPlayer.play();
	}

	volumeSlider.addEventListener("input", () => {
		audioPlayer.volume = volumeSlider.value;
	});

	audioPlayer.addEventListener("ended", () => {
		handleNext();
	});
});
