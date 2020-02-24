var el = x => document.getElementById(x);

function showPicker() {
  el("file-input").click();
}

function showPicked(input) {
  el("upload-label").innerHTML = input.files[0].name;
  var reader = new FileReader();
  reader.onload = function(e) {
    el("image-picked").src = e.target.result;
    el("image-picked").className = "";
  };
  reader.readAsDataURL(input.files[0]);
}

function analyze() {
  var uploadFiles = el("file-input").files;
  if (uploadFiles.length !== 1) alert("Please select a file to analyze!");

  el("analyze-button").innerHTML = "Analyzing...";
  var xhr = new XMLHttpRequest();
  var loc = window.location;
  xhr.open(
    "POST",
    `${loc.protocol}//${loc.hostname}:${loc.port}/analyze`,
    true
  );
  xhr.onerror = function() {
    alert(xhr.responseText);
  };
  xhr.onload = function(e) {
    if (this.readyState === 4) {
      var response = JSON.parse(e.target.responseText);
      // el("result-label").innerHTML = `Result = ${response["title"]}`;
      el("image-picked").src = response["image"];
      el("image-recommend-link").href = response["link"];
      el("title").innerHTML = response["title"];
      el("price").innerHTML = `$response["price"] USD`;
      el("upload-label").innerHTML =
        "Click on the image below to go to Mejuri!!";
      el("analyze-button").innerHTML = "Done";
    }
  };

  var fileData = new FormData();
  fileData.append("file", uploadFiles[0]);
  xhr.send(fileData);
}
