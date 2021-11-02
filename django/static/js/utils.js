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

      //console.log('changing the menu')
      
      //document.forms["sampleForm"].submit();
      //console.log('changed')
      if (neuroglancer_window.style.width != "75%" ) {
        openSideMenu()
        //console.log('sending form')
        document.sidebar_form.sidebar_tab.value = 'open';
        document.forms["sidebar_form"].submit();
      } else {
        closeSideMenu()
        document.sidebar_form.sidebar_tab.value = 'closed';
        document.forms["sidebar_form"].submit();
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











