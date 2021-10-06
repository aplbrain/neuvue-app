function block_toggle() {

  var acc = document.getElementsByClassName("taskButton");
  var i;

  for (i = 0; i < acc.length; i++) {
    acc[i].addEventListener("click", function() {
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
    });
  }
}

/* This controls information from appearing in the sidebar*/
function sidemenu_content() {

  var i_button = document.getElementById("instruction-button");
  var i_container = document.getElementById("instruction-container");
  var q_button = document.getElementById("queue-button");
  var q_container = document.getElementById("queue-container");
  var neuroglancer_window = document.getElementById("neuroglancer");
  
  
  i_button.onclick=function() {

    

    /* Toggle between adding and removing the "active" class,
    to highlight the button that controls the panel */
    this.classList.toggle("active");

    if (i_container.style.visibility != "visible") {
      if (neuroglancer_window.style.width != "75%" ) {
        openSideMenu()
      }
      i_container.style.visibility = "visible";
      q_container.style.visibility = "hidden";
      
    } else {
      if (neuroglancer_window.style.width === "75%" ) {
        closeSideMenu()
      }
      i_container.style.visibility = "hidden";
    } 

  };

  q_button.onclick=function() {


    /* Toggle between adding and removing the "active" class,
    to highlight the button that controls the panel */
    this.classList.toggle("active");

    if (q_container.style.visibility != "visible") {
      if (neuroglancer_window.style.width != "75%" ) {
        openSideMenu()
      }
      q_container.style.visibility = "visible";
      i_container.style.visibility = "hidden";
      
    } else {
      if (neuroglancer_window.style.width === "75%" ) {
        closeSideMenu()
      }
      q_container.style.visibility = "hidden";

    }
  };

}
function openSideMenu(){
  var sidemenu = document.getElementById("neuVue-sidemenu");
  var sidebar = document.getElementById("neuVue-sidebar");
  var sidecontent = document.getElementById("neuVue-sidecontent");
  var neuroglancer_window = document.getElementById("neuroglancer");

  sidemenu.style.width = "25%";
  sidebar.style.width = "12%";
  sidecontent.style.width = "80%";
  sidecontent.style.visibility = "visible";

  sidemenu.style.transition = "0.3s";
  sidebar.style.transition = "0.15s";
  sidecontent.style.animationDelay = "0.29s";

  
  neuroglancer_window.style.width = "75%";

}

function closeSideMenu() {
  var sidemenu = document.getElementById("neuVue-sidemenu");
  var sidebar = document.getElementById("neuVue-sidebar");
  var sidecontent = document.getElementById("neuVue-sidecontent");
  var neuroglancer_window = document.getElementById("neuroglancer");

  sidemenu.style.width = "2%";
  sidebar.style.width = "100%";
  sidecontent.style.width = "0%";
  sidecontent.style.visibility = "hidden";

  sidemenu.style.transition = "0.3s";
  sidebar.style.transitionDelay = "0.15s";
  sidecontent.style.transition = "0.3s";

  
  neuroglancer_window.style.width = "96%";
}

/* FOR TAKS PAGE */

function table_toggle() {

  var acc = document.getElementsByClassName("jobHeader");
  var i;

  for (i = 0; i < acc.length; i++) {
    acc[i].addEventListener("click", function() {
      /* Toggle between adding and removing the "active" class,
      to highlight the button that controls the panel */
      this.classList.toggle("active");

      /* Toggle between hiding and showing the active panel */
      var panel = this.nextElementSibling;
      if (panel.style.display == "block") {
        panel.style.display = "none";
      } else {
        panel.style.display = "block";
      }
    });
  }
}





