// ===============================
// Notifications Page JavaScript
// ===============================

const searchInput = document.getElementById("searchNotification");
const filterSelect = document.getElementById("filterNotification");
const notifications = document.querySelectorAll(".notification");
const markAllBtn = document.getElementById("markAll");
const deleteAllBtn = document.getElementById("deleteAll");

const totalCount = document.getElementById("totalCount");
const readCount = document.getElementById("readCount");
const unreadCount = document.getElementById("unreadCount");

// ===============================
// Update Counter
// ===============================

function updateCounter(){

const cards = document.querySelectorAll(".notification");

let total = cards.length;
let unread = document.querySelectorAll(".notification.unread").length;
let read = total - unread;

totalCount.textContent = total;
readCount.textContent = read;
unreadCount.textContent = unread;

}

updateCounter();

// ===============================
// Search Notification
// ===============================

searchInput.addEventListener("keyup",function(){

const value = this.value.toLowerCase();

notifications.forEach(card=>{

const text = card.innerText.toLowerCase();

card.style.display = text.includes(value) ? "flex" : "none";

});

});

// ===============================
// Filter Notification
// ===============================

filterSelect.addEventListener("change",function(){

const value = this.value;

notifications.forEach(card=>{

if(value==="all"){

card.style.display="flex";

}

else if(value==="unread"){

card.style.display=
card.classList.contains("unread")
?"flex":"none";

}

else if(value==="read"){

card.style.display=
card.classList.contains("unread")
?"none":"flex";

}

else{

card.style.display="flex";

}

});

});

// ===============================
// Mark All Read
// ===============================

markAllBtn.addEventListener("click",()=>{

notifications.forEach(card=>{

card.classList.remove("unread");

const badge = card.querySelector(".badge");

badge.innerHTML="Read";

badge.classList.remove("unread-badge");

badge.classList.add("read-badge");

});

updateCounter();

alert("All Notifications Marked As Read");

});

// ===============================
// Delete Single Notification
// ===============================

document.querySelectorAll(".deleteBtn").forEach(btn=>{

btn.addEventListener("click",function(){

this.closest(".notification").remove();

updateCounter();

});

});

// ===============================
// Delete All
// ===============================

deleteAllBtn.addEventListener("click",()=>{

if(confirm("Delete all notifications ?")){

document.querySelector(".notification-list").innerHTML="";

updateCounter();

}

});

// ===============================
// Click Notification -> Read
// ===============================

notifications.forEach(card=>{

card.addEventListener("click",function(e){

if(e.target.closest(".deleteBtn")) return;

this.classList.remove("unread");

const badge=this.querySelector(".badge");

badge.innerHTML="Read";

badge.classList.remove("unread-badge");

badge.classList.add("read-badge");

updateCounter();

});

});

// ===============================
// Welcome Message
// ===============================

window.onload=()=>{

console.log("Notifications Loaded Successfully");

};