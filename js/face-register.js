/*==========================================
 FACE REGISTER
==========================================*/

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const preview = document.getElementById("previewImage");

const captureBtn = document.getElementById("captureBtn");
const registerBtn = document.getElementById("registerBtn");
const resetBtn = document.getElementById("resetBtn");

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

        statusBox.innerHTML = "📷 Camera Started Successfully";

    }

    catch(error){

        console.error(error);

        statusBox.innerHTML = "❌ Unable to access camera";

    }

}

startCamera();

/*==========================================
 CAPTURE IMAGE
==========================================*/

captureBtn.addEventListener("click",()=>{

    const ctx = canvas.getContext("2d");

    canvas.width = video.videoWidth;

    canvas.height = video.videoHeight;

    ctx.drawImage(video,0,0,canvas.width,canvas.height);

    capturedImage = canvas.toDataURL("image/png");

    preview.src = capturedImage;

    preview.style.display = "block";

    statusBox.innerHTML = "✅ Face Captured Successfully";

});

/*==========================================
 RESET
==========================================*/

resetBtn.addEventListener("click",()=>{

    preview.src = "";

    preview.style.display = "none";

    capturedImage = null;

    statusBox.innerHTML = "🔄 Ready to Capture Again";

});

/*==========================================
 REGISTER
==========================================*/

registerBtn.addEventListener("click",()=>{

    if(capturedImage==null){

        alert("Please Capture Face First");

        return;

    }

    statusBox.innerHTML = "⏳ Registering Face...";

});
/*==========================================
 FORM VALIDATION
==========================================*/

const registerForm = document.getElementById("registerForm");

registerForm.addEventListener("submit",function(e){

    e.preventDefault();

    if(capturedImage==null){

        alert("Please Capture Face First");

        return;

    }

    const name=document.getElementById("name").value.trim();
    const id=document.getElementById("teacherId").value.trim();
    const dept=document.getElementById("department").value;

    if(name==="" || id==="" || dept===""){

        alert("Please fill all required fields.");

        return;

    }

    saveFace(name,id,dept);

});

/*==========================================
 SAVE FACE DATA
==========================================*/

function saveFace(name,id,dept){

    const teacher={

        name:name,

        teacherId:id,

        department:dept,

        faceImage:capturedImage,

        createdAt:new Date().toLocaleString()

    };

    localStorage.setItem("registeredTeacher",JSON.stringify(teacher));

    statusBox.innerHTML="✅ Face Registered Successfully";

    alert("Face Registration Completed Successfully.");

}

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

/*==========================================
 PAGE EXIT
==========================================*/

window.addEventListener("beforeunload",()=>{

    stopCamera();

});

/*==========================================
 CLEAR FORM
==========================================*/

function clearForm(){

    registerForm.reset();

    preview.src="";

    preview.style.display="none";

    capturedImage=null;

    statusBox.innerHTML="📷 Ready for New Registration";

}

resetBtn.addEventListener("click",clearForm);

/*==========================================
 AUTO HIDE MESSAGE
==========================================*/

function showMessage(message){

    statusBox.innerHTML=message;

    setTimeout(()=>{

        statusBox.innerHTML="📷 Ready";

    },3000);

}

/*==========================================
 SUCCESS EFFECT
==========================================*/

registerBtn.addEventListener("click",()=>{

    if(capturedImage){

        showMessage("✅ Registration Successful");

    }

});