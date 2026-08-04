/*==========================================
 FACE ATTENDANCE
==========================================*/

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const markBtn = document.getElementById("markBtn");

const statusBox = document.getElementById("statusBox");

let stream = null;
let attendanceImage = null;

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

        console.log(error);

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

    statusBox.innerHTML = "🛑 Camera Stopped";

});

/*==========================================
 CAPTURE FACE
==========================================*/

function captureFace(){

    const ctx = canvas.getContext("2d");

    canvas.width = video.videoWidth;

    canvas.height = video.videoHeight;

    ctx.drawImage(video,0,0,canvas.width,canvas.height);

    attendanceImage = canvas.toDataURL("image/png");

    return attendanceImage;

}

/*==========================================
 MARK ATTENDANCE
==========================================*/

markBtn.addEventListener("click",()=>{

    if(!stream){

        alert("Please Start Camera First");

        return;

    }

    captureFace();

    statusBox.innerHTML = "🔍 Scanning Face...";

});

/*==========================================
 MATCH FACE
==========================================*/

function matchFace(){

    const savedTeacher =
        JSON.parse(localStorage.getItem("registeredTeacher"));

    if(!savedTeacher){

        statusBox.innerHTML = "❌ No Registered Face Found";

        return false;

    }

    /* Demo Matching
       Replace this with OpenCV/CNN API later */

    return true;

}

/*==========================================
 SAVE ATTENDANCE
==========================================*/

function saveAttendance(){

    const teacher =
        JSON.parse(localStorage.getItem("registeredTeacher"));

    if(!teacher) return;

    let attendance =
        JSON.parse(localStorage.getItem("attendance")) || [];

    attendance.push({

        teacherId:teacher.teacherId,

        name:teacher.name,

        department:teacher.department,

        date:new Date().toLocaleDateString(),

        time:new Date().toLocaleTimeString(),

        status:"Present"

    });

    localStorage.setItem(
        "attendance",
        JSON.stringify(attendance)
    );

}

/*==========================================
 MARK ATTENDANCE
==========================================*/

markBtn.addEventListener("click",()=>{

    if(!attendanceImage){

        captureFace();

    }

    if(matchFace()){

        saveAttendance();

        statusBox.innerHTML =
            "✅ Attendance Marked Successfully";

        alert("Attendance Marked Successfully.");

    }

    else{

        statusBox.innerHTML =
            "❌ Face Not Recognized";

        alert("Face Not Matched.");

    }

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
            "📷 Ready For Face Scan";

    },3000);

}

markBtn.addEventListener("click",resetStatus);

/*==========================================
 AUTO START (OPTIONAL)
==========================================*/

// Uncomment if you want camera to start automatically

// startCamera();