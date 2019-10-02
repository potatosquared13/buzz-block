window.onload = () => {
  document.getElementById("time").innerHTML = (new Date()).toLocaleString();
}

function getVendorTransactions(vendor_id) {
  window.location.href = `/get_vendor_transactions?vendor=${vendor_id}`;
}