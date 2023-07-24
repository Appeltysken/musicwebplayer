"use strict";

document.addEventListener("DOMContentLoaded", () => {
	const searchInput = document.getElementById("search-input");
	const searchResults = document.getElementById("search-results");
	const audioPlayer = document.getElementById("audio-player");
	const playButton = document.getElementById("play-button");
	const volumeSlider = document.getElementById("volume-slider");
	const currentTimeElement = document.getElementById("current-time");
	const durationElement = document.getElementById("duration");
	const timeSlider = document.getElementById("time-slider");

	let currentTrackIndex = 0;
	let tracks = [];

	/**
	 * Функция обрабатывает клики пользователя на странице.
	 * Если была нажата кнопка "Поиск", то запускается функция handleSearch.
	 * Если была нажата кнопка "Предыдущий трек", то запускается функция handlePrev.
	 * Если была нажата кнопка "Воспроизведение/Пауза", то запускается функция handlePlay.
	 * Если была нажата кнопка "Следующий трек", то запускается функция handleNext.
	 * @param {Object} event - Объект события клика.
	 * @returns {void}
	 */
	document.addEventListener("click", (event) => {
		if (event.target.id === "search-button") {
			handleSearch();
		} else if (event.target.closest("#prev-button")) {
			handlePrev();
		} else if (event.target.closest("#play-button")) {
			handlePlay();
		} else if (event.target.closest("#next-button")) {
			handleNext();
		}
	});

	/**
	 * Функция сохраняет состояние плеера в локальное хранилище перед закрытием страницы.
	 * Состояние плеера включает в себя индекс текущего трека, список треков, текущее время воспроизведения,
	 * а также информацию о том, проигрывается ли в данный момент трек.
	 * @returns {void}
	 */
	window.addEventListener("beforeunload", () => {
		const state = {
			currentTrackIndex,
			tracks,
			currentTime: audioPlayer.currentTime,
			isPlaying: !audioPlayer.paused,
			volume: audioPlayer.volume,
		};
		localStorage.setItem("musicPlayerState", JSON.stringify(state));
	});

	/**
	 * Функция handleSearch осуществляет поиск треков по введенному пользователем запросу.
	 * Если результаты поиска уже были закешированы, то они берутся из локального хранилища.
	 * Если результаты не были закешированы, то они запрашиваются у API и сохраняются в локальном хранилище.
	 * После получения результатов поиска, функция фильтрует треки по запросу и отображает первый найденный трек.
	 * @returns {Promise<void>}
	 */
	async function handleSearch() {
		const searchTerm = searchInput.value.toLowerCase();
		try {
			let results = [];
			const cachedResults = localStorage.getItem(searchTerm);
			if (cachedResults) {
				results = JSON.parse(cachedResults);
			} else {
				const response = await fetch(
					`https://api.jamendo.com/v3.0/tracks/?client_id=4cb570af&format=json&limit=10&search=${searchTerm}&order=relevance`,
				);
				const data = await response.json();
				results = data.results;
				localStorage.setItem(searchTerm, JSON.stringify(results));
			}

			tracks = results.filter((track) => {
				const trackName = track.name.toLowerCase();
				const artistName = track.artist_name.toLowerCase();
				return trackName.includes(searchTerm) || artistName.includes(searchTerm);
			});

			if (tracks.length === 0) {
				searchResults.innerHTML = "<li>По вашему запросу ничего не найдено.</li>";
			} else {
				currentTrackIndex = 0;
				displayTrack(tracks[currentTrackIndex]);
				updateAudioSource(tracks[currentTrackIndex].audio);
				updateTrackInfo(tracks[currentTrackIndex]);
			}
		} catch (error) {
			console.error("При поиске трека произошла ошибка:", error);
		}
	}

	/**
	 * Функция displayTrack отображает информацию о найденном треке на странице.
	 * @param {Object} track - Объект, содержащий информацию о треке.
	 */
	function displayTrack(track) {
		searchResults.innerHTML = `<li>${track.name} — ${track.artist_name}</li>`;
	}

	/**
	 * Функция updateAudioSource обновляет источник аудио-плеера новым URL.
	 * @param {string} audioUrl - URL аудио-файла.
	 */
	function updateAudioSource(audioUrl) {
		audioPlayer.src = audioUrl;
		audioPlayer.load();
	}

	/**
	 * Функция updateTrackInfo обновляет информацию о треке на странице.
	 * @param {Object} track - Объект, содержащий информацию о треке.
	 */
	function updateTrackInfo(track) {
		const trackNameElement = document.getElementById("track-name");
		const artistNameElement = document.getElementById("artist-name");

		trackNameElement.textContent = track.name;
		artistNameElement.textContent = track.artist_name;
	}

	/**
	 * Функция добавляет обработчик события "input" на поле ввода поискового запроса.
	 * При изменении значения в поле ввода, функция handleSearch будет вызвана через 300 миллисекунд.
	 */
	searchInput.addEventListener("input", () => {
		setTimeout(handleSearch, 300);
	});

	/**
	 * Функция handlePrev переключает на предыдущий трек в списке найденных треков.
	 * Если воспроизведение было запущено, то оно останавливается.
	 */
	function handlePrev() {
		if (tracks.length === 0) return;
		currentTrackIndex = (currentTrackIndex - 1 + tracks.length) % tracks.length;
		displayTrack(tracks[currentTrackIndex]);
		updateAudioSource(tracks[currentTrackIndex].audio);
		updateTrackInfo(tracks[currentTrackIndex]);

		if (!audioPlayer.paused) {
			playButton.innerHTML = '<button id="play-button" class="player-controls"><i class="fas fa-pause"></i></button>';
			audioPlayer.play();
		} else {
			playButton.innerHTML = '<button id="play-button" class="player-controls"><i class="fas fa-play"></i></button>';
		}
	}

	/**
	 * Функция handlePlay обрабатывает нажатие на кнопку воспроизведения/паузы аудио-плеера.
	 * Если список найденных треков пуст, функция завершается.
	 * Если аудио-плеер на паузе, функция запускает воспроизведение и меняет иконку на кнопке на "паузу".
	 * Если аудио-плеер воспроизводит аудио, функция останавливает воспроизведение и меняет иконку на кнопке на "воспроизведение".
	 */
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

	/**
	 * Функция handleNext переключает на следующий трек в списке найденных треков.
	 * Если воспроизведение было запущено, то оно продолжается.
	 * Если список найденных треков пуст, функция завершается.
	 */
	function handleNext() {
		if (tracks.length === 0) return;
		const wasPaused = audioPlayer.paused;
		currentTrackIndex = (currentTrackIndex + 1) % tracks.length;
		displayTrack(tracks[currentTrackIndex]);
		updateAudioSource(tracks[currentTrackIndex].audio);
		updateTrackInfo(tracks[currentTrackIndex]);

		audioPlayer.addEventListener(
			"canplay",
			() => {
				audioPlayer.currentTime = 0;
				audioPlayer.play();
				playButton.innerHTML = '<button id="play-button" class="player-controls"><i class="fas fa-pause"></i></button>';
			},
			{ once: true },
		);

		if (!wasPaused) {
			audioPlayer.play();
			playButton.innerHTML = '<button id="play-button" class="player-controls"><i class="fas fa-pause"></i></button>';
		}
	}

	/**
	 * Функция добавляет обработчик события "input" на ползунок громкости аудио-плеера.
	 * При изменении значения ползунка, функция устанавливает громкость аудио-плеера в соответствии с новым значением ползунка.
	 */
	volumeSlider.addEventListener("input", () => {
		audioPlayer.volume = volumeSlider.value;
	});

	/**
	 * Функция добавляет обработчик события "ended" на аудио-плеер.
	 * При окончании воспроизведения текущего трека, функция переключает на следующий трек в списке найденных треков.
	 */
	audioPlayer.addEventListener("ended", () => {
		handleNext();
	});

	/**
	 * Функция обновляет элементы интерфейса, связанные с продолжительностью аудио-файла.
	 * При событии "canplaythrough" на аудио-плеере, функция устанавливает продолжительность аудио-файла в элементе durationElement,
	 * а также устанавливает максимальное значение ползунка времени воспроизведения в соответствии с продолжительностью аудио-файла.
	 */
	audioPlayer.addEventListener("canplaythrough", () => {
		const duration = audioPlayer.duration;
		durationElement.textContent = formatTime(duration);
		timeSlider.max = duration;
	});

	/**
	 * Функция updateCurrentTime обновляет текущее время воспроизведения аудио-файла и положение ползунка времени воспроизведения.
	 * Функция вызывается при каждом обновлении времени воспроизведения аудио-файла.
	 */
	let animationFrameId;
	function updateCurrentTime() {
		const currentTime = audioPlayer.currentTime;
		currentTimeElement.textContent = formatTime(currentTime);
		timeSlider.value = currentTime;
		animationFrameId = requestAnimationFrame(updateCurrentTime);
	}

	/**
	 * Функция добавляет обработчик события "input" на ползунок времени воспроизведения аудио-плеера.
	 * При изменении значения ползунка, функция устанавливает текущее время воспроизведения аудио-файла в соответствии с новым значением ползунка.
	 */
	timeSlider.addEventListener("input", () => {
		const seekTime = parseFloat(timeSlider.value);
		audioPlayer.currentTime = seekTime;
	});

	/**
	 * Функция formatTime принимает время в секундах и возвращает его в формате "минуты:секунды".
	 * @param {number} time - время в секундах.
	 * @returns {string} - время в формате "минуты:секунды".
	 */
	function formatTime(time) {
		const date = new Date(time * 1000);
		const minutes = date.getUTCMinutes().toString().padStart(2, "0");
		const seconds = date.getUTCSeconds().toString().padStart(2, "0");
		return `${minutes}:${seconds}`;
	}

	/**
	 * Добавляет обработчик события "play" на аудио-плеер.
	 * При запуске воспроизведения аудио-файла, функция запускает обновление текущего времени воспроизведения аудио-файла.
	 */
	audioPlayer.addEventListener("play", () => {
		animationFrameId = requestAnimationFrame(updateCurrentTime);
	});

	/**
	 * Добавляет обработчик события "pause" на аудио-плеер.
	 * При остановке воспроизведения аудио-файла, функция отменяет обновление текущего времени воспроизведения аудио-файла.
	 */
	audioPlayer.addEventListener("pause", () => {
		cancelAnimationFrame(animationFrameId);
	});
});
