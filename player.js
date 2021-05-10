const container = document.querySelector('.container');
const prevBtn = document.querySelector('#prev');
const playBtn = document.querySelector('#play');
const nextBtn = document.querySelector('#next');
const audio = document.querySelector('#audio');
const progress = document.querySelector('.progress-bar');
const pContainer = document.querySelector('.progress-container');
const title = document.querySelector('#title');
const images = document.querySelector('#img');


const songs = ['brown_munde','cradles','zara'];
let songsIndex = 2;

loadSong(songs[songsIndex]);

function loadSong(song){
    title.innerHTML = song
    audio.src = `music/${song}.mp3`
    img.src = `images/${song}.jpg`
}

function playSong(){
    container.classList.add('play')
    playBtn.querySelector('i.fas').classList.remove('fa-play');
    playBtn.querySelector('i.fas').classList.add('fa-pause');
    audio.play();
}

function pauseSong(){
    container.classList.remove('play')
    playBtn.querySelector('i.fas').classList.add('fa-play');
    playBtn.querySelector('i.fas').classList.remove('fa-pause');
    audio.pause();

}
function prevSong(){
    songsIndex--

    if(songsIndex < 0){
        songsIndex = songs.length - 1;
    }
    loadSong(songs[songsIndex])

    playSong()
}

function nextSong(){
    songsIndex++;

    if(songsIndex > songs.length-1){
        songsIndex = 0
    }
    loadSong(songs[songsIndex]) 

    playSong()
}

function updateProgress(e){
    const{duration,currentTime} = e.srcElement
    const progressPercent = (currentTime/duration)*100
    progress.style.width = `${progressPercent}%`

}

function setProgress(e){
    const width = this.clientWidth
    const clickX = e.offsetX
    const duration = audio.duration
    
    audio.currentTime = (clickX / width) * duration


}
//event listeners
playBtn.addEventListener("click",() => {
    const isPlaying = container.classList.contains('play');

    if(isPlaying){
        pauseSong();
    }
    else{
        playSong();
    }
});

prevBtn.addEventListener('click',prevSong);
nextBtn.addEventListener('click',nextSong);

audio.addEventListener('timeupdate',updateProgress);

pContainer.addEventListener('click',setProgress);


audio.addEventListener('ended',nextSong);