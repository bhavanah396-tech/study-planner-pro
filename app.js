function startPomodoro(){

    let time = 1500;

    let timer = document.getElementById("timer");

    let interval = setInterval(()=>{

        let min = Math.floor(time/60);

        let sec = time % 60;

        timer.innerHTML =
        `${min}:${sec < 10 ? '0'+sec : sec}`;

        time--;

        if(time < 0){

            clearInterval(interval);

            alert("Pomodoro Complete!");

        }

    },1000);

}