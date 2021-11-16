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
      openSideMenu();
      // updateSideBar(1);
    } else {
      closeSideMenu();
      // updateSideBar(0);
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
}
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}
function updateSideBar(action) {
  
  const csrftoken = getCookie('csrftoken');

  const myInit = {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/plain, */*',
          'X-CSRFToken': csrftoken,
      },
      body: JSON.stringify({'sidebar_tab': action}),
      credentials: 'same-origin',
  };
  fetch('', myInit).then(function (response) {
      /*
      if (response.ok) {
          console.log('success')
      }
      else {
          console.log('failed')
      }
      */
  });
}


/* Flag Modal */
function toggleTextbox(){
    var reason=document.getElementById("select-flag");
    var textbox = document.getElementById("text")
    if(reason.value == "other")
        textbox.style.display = "block"
    else
        textbox.style.display = "none"
}

function copyToClipboard(copyInfo) {
   /* Copy the text inside the text field */
  navigator.clipboard.writeText(copyInfo);
}











