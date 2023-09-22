document.getElementById("upload_btn").addEventListener("click", function () {
    document.getElementById('uploadForm').style.display = "flex";
    document.getElementById('upload_btn').style.display = "none";
});
document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(t => new bootstrap.Tooltip(t));
document.getElementById("view0_btn").addEventListener("click", async function () {
    document.getElementById('view1_container').style.display = "none";
    document.getElementById('view0_container').style.display = "block";
    document.getElementById('view1_btn').removeAttribute("disabled");
    document.getElementById('view0_btn').setAttribute("disabled", true);
    await fetch('/changeView?view=0');
});
document.getElementById("view1_btn").addEventListener("click", async function () {
    document.getElementById('view0_container').style.display = "none";
    document.getElementById('view1_container').style.display = "block";
    document.getElementById('view0_btn').removeAttribute("disabled");
    document.getElementById('view1_btn').setAttribute("disabled", true);
    await fetch('/changeView?view=1');
});