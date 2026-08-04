/*==========================================
 FACE LOGIN
==========================================*/

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");

const startBtn = document.getElementById("startBtn");
const loginBtn = document.getElementById("loginBtn");
const stopBtn = document.getElementById("stopBtn");

const statusBox = document.getElementById("statusBox");

let stream = null;
let capturedImage = null;

/*==========================================
 START CAMERA
==========================================*/

async function startCamera(){

    try{

        stream = await navigator.mediaDevices.getUserMedia({

            video:true,

            audio:false

        });

        video.srcObject = stream;

        statusBox.innerHTML = "📷 Camera Started";

    }

    catch(error){

        console.error(error);

        statusBox.innerHTML = "❌ Camera Permission Denied";

    }

}

/*==========================================
 START BUTTON
==========================================*/

startBtn.addEventListener("click",()=>{

    startCamera();

});

/*==========================================
 STOP CAMERA
==========================================*/

stopBtn.addEventListener("click",()=>{

    if(stream){

        stream.getTracks().forEach(track=>{

            track.stop();

        });

    }

    statusBox.innerHTML="🛑 Camera Stopped";

});

/*==========================================
 CAPTURE FACE
==========================================*/

function captureFace(){

    const ctx=canvas.getContext("2d");

    canvas.width=video.videoWidth;

    canvas.height=video.videoHeight;

    ctx.drawImage(video,0,0,canvas.width,canvas.height);

    capturedImage=canvas.toDataURL("image/png");

    return capturedImage;

}
/*==========================================
 FACE MATCHING
==========================================*/

function matchFace(){

    const teacher =
        JSON.parse(localStorage.getItem("registeredTeacher"));

    if(!teacher){

        statusBox.innerHTML =
            "❌ No Registered Face Found";

        return false;

    }

    /* Demo Matching
       Replace with Python + OpenCV + CNN API */

    return true;

}

/*==========================================
 LOGIN
==========================================*/

loginBtn.addEventListener("click",()=>{

    if(!stream){

        alert("Please Start Camera First");

        return;

    }

    captureFace();

    statusBox.innerHTML =
        "🔍 Verifying Face...";

    setTimeout(()=>{

        if(matchFace()){

            const teacher =
                JSON.parse(localStorage.getItem("registeredTeacher"));

            localStorage.setItem("currentUser",
                JSON.stringify(teacher)
            );

            statusBox.innerHTML =
                "✅ Login Successful";

            alert("Welcome " + teacher.name);

            window.location.href =
                "teacher-dashboard.html";

        }

        else{

            statusBox.innerHTML =
                "❌ Face Not Recognized";

            alert("Face Verification Failed");

        }

    },2000);

});

/*==========================================
 STOP CAMERA
==========================================*/

function stopCamera(){

    if(stream){

        stream.getTracks().forEach(track=>{

            track.stop();

        });

    }

}

window.addEventListener("beforeunload",()=>{

    stopCamera();

});

/*==========================================
 RESET STATUS
==========================================*/

function resetStatus(){

    setTimeout(()=>{

        statusBox.innerHTML =
            "📷 Ready For Face Login";

    },3000);

}

loginBtn.addEventListener("click",resetStatus);

/*==========================================
 LOGOUT
==========================================*/

function logout(){

    localStorage.removeItem("currentUser");

    window.location.href =
        "../../index.html";

}

/*==========================================
 AUTO LOGIN CHECK
==========================================*/

const currentUser =
    JSON.parse(localStorage.getItem("currentUser"));

if(currentUser){

    console.log(
        "Logged In:",
        currentUser.name
    );

}