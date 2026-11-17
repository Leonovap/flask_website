document.addEventListener("DOMContentLoaded", () => {
    const lines = Array.from(document.querySelectorAll(".typewriter"));
    if (!lines.length) return;

    // 1. Srazu priachiem ves tekst v chernotu pered startom animacii
    const texts = lines.map(el => {
        const txt = el.getAttribute("data-text") || el.textContent || "";
        el.textContent = "";
        return txt;
    });

    // 2. Sozdaem odin nastoyashchii terminalnyi kursor
    const cursor = document.createElement("span");
    cursor.className = "cursor";
    cursor.textContent = "█";

    let lineIdx = 0;
    let charIdx = 0;

    function typeNextChar() {
        if (lineIdx >= lines.length) return;

        const currentLine = lines[lineIdx];
        const fullText = texts[lineIdx];

        // Derzhim kursor v konce tekushchei stroki
        if (cursor.parentNode !== currentLine) {
            currentLine.appendChild(cursor);
        }

        if (charIdx < fullText.length) {
            // Vstavlyaem bukvu pered kursorom
            cursor.before(fullText.charAt(charIdx));
            charIdx++;
            // Skorost pechati (20-35 ms — bistro i plavno, kak v terminale)
            setTimeout(typeNextChar, 40);
        } else {
            // Stroka napechatana — perehodim na sleduyushchuyu posle korotkoi pauzy
            lineIdx++;
            charIdx = 0;
            setTimeout(typeNextChar, 180);
        }
    }

    typeNextChar();
});