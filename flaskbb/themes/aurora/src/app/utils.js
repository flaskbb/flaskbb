export function isHidden(element) {
    return window.getComputedStyle(element).display === "none";
}

export function hideElement(element) {
    element.style.display = "none";
}

export function showElement(element) {
    element.style.display = "block";
}
