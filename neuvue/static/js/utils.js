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

function toggleNav() {
    var acc = document.getElementById("myNav");
    var bin = document.getElementById("neuroglancer")
    if (acc.style.width == "25%") {
        acc.style.width = "0%";
        bin.style.width = "100%";
    } else if (acc.style.width == "0%"){
        acc.style.width = "25%";
        bin.style.width = "75%";
    } else {
        acc.style.width = "0%";
        bin.style.width = "100%";
    }
}
