function toggleSidebar() {
    var sidebar = document.getElementById("sidebar");
    var mainContent = document.getElementById("main-content");
    var openButton = document.querySelector(".open-btn");
    var openButtonText = openButton.querySelector("span");
    
    var desiredWidth = '210px'; // サイドバーの幅

    var openButtonWidth = openButton.offsetWidth;
    var sidebarWidth = 210;

    if (sidebar.style.width === desiredWidth) {
        sidebar.style.width = '0';
        mainContent.style.marginLeft = '0';
        openButton.style.left = `-5px`;
        openButtonText.textContent = '探す';
    } else {
        sidebar.style.width = desiredWidth;
        mainContent.style.marginLeft = desiredWidth;
        openButton.style.left = `${sidebarWidth - 5}px`;
        openButtonText.textContent = '閉じる';
    }
}
document.addEventListener('click', function(event) {
    var sidebar = document.getElementById("sidebar");
    var openButton = document.querySelector(".open-btn");
    if (!sidebar.contains(event.target) && !openButton.contains(event.target) && sidebar.style.width === '210px') {
        toggleSidebar();
    }
});