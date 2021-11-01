/* Toggles the Small Drop Down Menus in the Task Queue List */
function block_toggle() {

  var acc = document.getElementsByClassName("taskButton");
  var i;

  for (i = 0; i < acc.length; i++) {
    acc[i].onclick=function() {
      /* Toggle between adding and removing the "active" class,
      to highlight the button that controls the panel */
      this.classList.toggle("active");

      /* Toggle between hiding and showing the active panel */
      var panel = this.nextElementSibling;
      if (panel.style.display === "block") {
        panel.style.display = "none";
      } else {
        panel.style.display = "block";
      }
    };
  }
}

/* This controls information from appearing in the sidebar*/

function sidemenu_content() {
    var side_button = document.getElementById("sidebarActivate");
    var neuroglancer_window = document.getElementById("neuroglancer");

    /* Toggle between adding and removing the "active" class,
    to highlight the button that controls the panel */
    side_button.classList.toggle("active");

    
      if (neuroglancer_window.style.width != "75%" ) {
        openSideMenu()
      } else {
        closeSideMenu()
      }

} 

/* Opens Side Menu */
function openSideMenu(){
  var sidemenu = document.getElementById("neuVue-sidemenu");
  var sidebar = document.getElementById("neuVue-sidebar");
  var sidecontent = document.getElementById("neuVue-sidecontent");
  var neuroglancer_window = document.getElementById("neuroglancer");

  sidemenu.style.width = "25%";
  sidebar.style.width = "8%";
  sidecontent.style.width = "85%";
  sidecontent.style.visibility = "visible";

  sideBoxes = document.getElementsByClassName("instructionBox");
  for (i = 0; i < sideBoxes.length; i++) {
      sideBoxes[i].style.visibility = "visible";
  }

  sidemenu.style.transition = "0.3s";
  sidebar.style.transition = "0.15s";
  sidecontent.style.animationDelay = "0.29s";

  neuroglancer_window.style.width = "75%";
  neuroglancer_window.style.left = "0%";
  document.cookie = "menu=open" /* Cookie handling */
}
/* Closes Side Menu */
function closeSideMenu() {
  var sidemenu = document.getElementById("neuVue-sidemenu");
  var sidebar = document.getElementById("neuVue-sidebar");
  var sidecontent = document.getElementById("neuVue-sidecontent");
  var neuroglancer_window = document.getElementById("neuroglancer");

  sidemenu.style.width = "2%";
  sidebar.style.width = "100%";
  sidecontent.style.width = "0%";
  sidecontent.style.visibility = "hidden";

  sideBoxes = document.getElementsByClassName("instructionBox");
  for (i = 0; i < sideBoxes.length; i++) {
      sideBoxes[i].style.visibility = "hidden";
  }

  sidemenu.style.transition = "0.3s";
  sidebar.style.transitionDelay = "0.15s";
  sidecontent.style.transition = "0.3s";

  
  neuroglancer_window.style.width = "101%";
  neuroglancer_window.style.left = "-2%";
  document.cookie = "menu=closed" /* Cookie handling */
}

/* Cookie handling */
function setCookie(cname, cvalue, exdays) {
  const d = new Date();
  d.setTime(d.getTime() + (exdays*24*60*60*1000));
  let expires = "expires="+ d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

/* Cookie handling */
function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}













