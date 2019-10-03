function registerClient() {

  let name = document.getElementById('client-name').value;
  let amount = document.getElementById('client-amount').value;
  let contactNumber = document.getElementById('client-contact').value;
  let url = `/register_client?name=${name}&amount=${amount}&contact=${contactNumber}`;

  let xhr = new XMLHttpRequest();

  xhr.open('POST', url, true);
  xhr.send()

  name = document.getElementById('client-name').value = "";
  amount = document.getElementById('client-amount').value = "";
  contactNumber = document.getElementById('client-contact').value = "";
}

function registerVendor() {

  let name = document.getElementById('vendor-name').value;
  let contactNumber = document.getElementById('vendor-contact').value;
  let url = `/register_vendor?name=${name}&contact=${contactNumber}`;

  let xhr = new XMLHttpRequest();

  xhr.open('POST', url, true);
  xhr.send()

  name = document.getElementById('vendor-name').value = "";
  contactNumber = document.getElementById('vendor-contact').value = "";
}

function finalize() {
  window.location.href = '/finalize';
}

// function vendor() {
//   var v = document.getElementById("vendor-container")
//   if (v.style.display === "none") {
//     v.style.display = "block";
//     document.getElementById("vendor-reg").classList.add("active");

//     document.getElementById("client-container").style.display = "none";
//     document.getElementById("client-reg").classList.remove("active");
//   }
// }

// function client() {
//   var c = document.getElementById("client-container")
//   if (c.style.display === "none") {
//     c.style.display = "block";
//     document.getElementById("client-reg").classList.add("active");

//     document.getElementById("vendor-container").style.display = "none";
//     document.getElementById("vendor-reg").classList.remove("active");
//   }
// }