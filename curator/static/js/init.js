document.getElementById("uploadButton").addEventListener("click", function () {
    document.getElementById('uploadForm').style.display = "block";
    document.getElementById('uploadButton').style.display = "none";
});
document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(t => new bootstrap.Tooltip(t));
document.getElementById("view0_button").addEventListener("click", async function () {
    document.getElementById('view1_container').style.display = "none";
    document.getElementById('view0_container').style.display = "block";
    document.getElementById('view1_button').removeAttribute("disabled");
    document.getElementById('view0_button').setAttribute("disabled", true);
    await fetch('/changeView?view=0');
});
document.getElementById("view1_button").addEventListener("click", async function () {
    document.getElementById('view0_container').style.display = "none";
    document.getElementById('view1_container').style.display = "block";
    document.getElementById('view0_button').removeAttribute("disabled");
    document.getElementById('view1_button').setAttribute("disabled", true);
    await fetch('/changeView?view=1');
});