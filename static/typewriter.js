document.addEventListener("DOMContentLoaded", () => {
  const lines = document.querySelectorAll(".typewriter");
  let lineIndex = 0;

  function typeLine(el, text, callback) {
    let charIndex = 0;
    el.textContent = ""; // Сlear text before printing
    const typingSpeed = 50;

    function typeChar() {
      if (charIndex < text.length) {
        el.textContent += text.charAt(charIndex);
        charIndex++;
        setTimeout(typeChar, typingSpeed);
      } else {
        if (callback) callback();
      }
    }
    typeChar();
  }

  function typeAllLines() {
    if (lineIndex < lines.length) {
      const el = lines[lineIndex];
      const text = el.getAttribute("data-text") || el.textContent;
      typeLine(el, text, () => {
        lineIndex++;
        typeAllLines();
      });
    }
  }
  typeAllLines();
});
