window.onload = () => {

  setInterval(() => {
    update();
  }, 10000);

}

function update() {

  let xhr = new XMLHttpRequest();

  xhr.open('GET', '/overview', true);
  xhr.send();

}