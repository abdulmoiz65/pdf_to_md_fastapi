/* ===================================================================
   PDF to Markdown Converter  |  Client-side logic
   =================================================================== */

(function () {
    "use strict";

    // -- DOM refs -------------------------------------------------------
    var dropZone = document.getElementById("drop-zone");
    var fileInput = document.getElementById("file-input");
    var fileInfo = document.getElementById("file-info");
    var fileName = document.getElementById("file-name");
    var fileSize = document.getElementById("file-size");
    var btnRemove = document.getElementById("btn-remove");
    var btnConvert = document.getElementById("btn-convert");
    var btnText = document.getElementById("btn-text");
    var btnLoader = document.getElementById("btn-loader");
    var errorMsg = document.getElementById("error-msg");
    var passwordInput = document.getElementById("password-input");

    var resultSection = document.getElementById("result-section");
    var uploadSection = document.getElementById("upload-section");
    var previewPane = document.getElementById("preview-container");
    var rawPane = document.getElementById("raw-md");
    var metaGrid = document.getElementById("meta-grid");
    var btnCopy = document.getElementById("btn-copy");
    var btnDownload = document.getElementById("btn-download");
    var btnNew = document.getElementById("btn-new");
    var tabs = document.querySelectorAll(".tab");
    var panes = document.querySelectorAll(".tab-content");

    var selectedFile = null;
    var markdownResult = "";
    var mdFilename = "output.md";

    // -- Show / hide helpers (use inline style) -------------------------
    function show(el) { if (el) el.style.display = ""; }
    function hide(el) { if (el) el.style.display = "none"; }

    // -- Toast notification ---------------------------------------------
    function toast(msg) {
        var el = document.querySelector(".toast");
        if (!el) {
            el = document.createElement("div");
            el.className = "toast";
            document.body.appendChild(el);
        }
        el.textContent = msg;
        // Force a reflow before adding .show so the transition fires
        void el.offsetWidth;
        el.classList.add("show");
        setTimeout(function () { el.classList.remove("show"); }, 2400);
    }

    // -- Size formatter -------------------------------------------------
    function fmtSize(bytes) {
        if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
        if (bytes >= 1024) return (bytes / 1024).toFixed(1) + " KB";
        return bytes + " B";
    }

    // -- File selection -------------------------------------------------
    function selectFile(file) {
        if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
            showError("Please select a valid PDF file.");
            return;
        }
        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = fmtSize(file.size);
        show(fileInfo);
        btnConvert.disabled = false;
        hideError();
    }

    // Click on drop zone => open file picker
    dropZone.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        fileInput.click();
    });

    fileInput.addEventListener("change", function (e) {
        if (e.target.files && e.target.files[0]) selectFile(e.target.files[0]);
    });

    // Drag & drop
    dropZone.addEventListener("dragenter", function (e) { e.preventDefault(); dropZone.classList.add("dragover"); });
    dropZone.addEventListener("dragover", function (e) { e.preventDefault(); dropZone.classList.add("dragover"); });
    dropZone.addEventListener("dragleave", function (e) { e.preventDefault(); dropZone.classList.remove("dragover"); });
    dropZone.addEventListener("drop", function (e) {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files[0]) selectFile(e.dataTransfer.files[0]);
    });

    // Remove file
    btnRemove.addEventListener("click", function (e) {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = "";
        hide(fileInfo);
        btnConvert.disabled = true;
    });

    // -- Error helpers --------------------------------------------------
    function showError(msg) { errorMsg.textContent = msg; show(errorMsg); }
    function hideError() { hide(errorMsg); }

    // -- Convert --------------------------------------------------------
    btnConvert.addEventListener("click", function () {
        if (!selectedFile) return;
        hideError();

        // UI => loading state
        hide(btnText);
        show(btnLoader);
        btnConvert.disabled = true;

        var form = new FormData();
        form.append("file", selectedFile);
        form.append("password", passwordInput.value || "");

        fetch("/api/convert", { method: "POST", body: form })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (!data.success) {
                    showError(data.error || "Conversion failed.");
                    return;
                }

                markdownResult = data.markdown;
                mdFilename = data.filename || "output.md";

                // Render preview
                previewPane.innerHTML = mdToHtml(markdownResult);
                rawPane.textContent = markdownResult;
                renderMeta(data.metadata);

                // Show result section
                show(resultSection);
                resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
            })
            .catch(function (err) {
                showError("Network error: " + err.message);
            })
            .finally(function () {
                show(btnText);
                hide(btnLoader);
                btnConvert.disabled = false;
            });
    });

    // -- Tabs -----------------------------------------------------------
    for (var i = 0; i < tabs.length; i++) {
        tabs[i].addEventListener("click", function () {
            for (var j = 0; j < tabs.length; j++)  tabs[j].classList.remove("active");
            for (var j = 0; j < panes.length; j++) panes[j].classList.remove("active");
            this.classList.add("active");
            var pane = document.getElementById("pane-" + this.getAttribute("data-tab"));
            if (pane) pane.classList.add("active");
        });
    }

    // -- Copy -----------------------------------------------------------
    btnCopy.addEventListener("click", function () {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(markdownResult).then(function () {
                toast("Copied to clipboard!");
            });
        } else {
            var ta = document.createElement("textarea");
            ta.value = markdownResult;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            toast("Copied to clipboard!");
        }
    });

    // -- Download -------------------------------------------------------
    btnDownload.addEventListener("click", function () {
        var blob = new Blob([markdownResult], { type: "text/markdown;charset=utf-8" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = mdFilename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast("Download started!");
    });

    // -- Convert another ------------------------------------------------
    btnNew.addEventListener("click", function () {
        hide(resultSection);
        selectedFile = null;
        fileInput.value = "";
        hide(fileInfo);
        btnConvert.disabled = true;
        markdownResult = "";
        passwordInput.value = "";
        uploadSection.scrollIntoView({ behavior: "smooth" });
    });

    // -- Metadata renderer ----------------------------------------------
    function renderMeta(meta) {
        if (!meta || typeof meta !== "object") {
            metaGrid.innerHTML = "<p>No metadata available.</p>";
            return;
        }
        var labels = {
            title: "Title", author: "Author", subject: "Subject", creator: "Creator",
            creation_date: "Created", modified_date: "Modified", pages: "Pages", encrypted: "Encrypted"
        };
        var html = "";
        var keys = Object.keys(labels);
        for (var i = 0; i < keys.length; i++) {
            var k = keys[i];
            var v = meta[k];
            if (v === undefined || v === "") continue;
            html += '<div class="meta-item">' +
                '<div class="meta-label">' + labels[k] + '</div>' +
                '<div class="meta-value">' + v + '</div>' +
                '</div>';
        }
        metaGrid.innerHTML = html || "<p>No metadata available.</p>";
    }

    // -- Simple Markdown to HTML ----------------------------------------
    function mdToHtml(md) {
        var html = md;

        // Remove YAML frontmatter
        html = html.replace(/^---[\s\S]*?---\n*/m, "");

        // Code blocks
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function (_, lang, code) {
            return '<pre><code>' + esc(code) + '</code></pre>';
        });

        // Headings (process longest first)
        html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
        html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
        html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
        html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

        // Horizontal rule
        html = html.replace(/^\s*---\s*$/gm, "<hr>");

        // Bold + italic
        html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
        html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

        // Images
        html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">');

        // Links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

        // Blockquotes
        html = html.replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>");

        // Tables
        html = html.replace(/^(\|.+\|)\n(\|[\s\-:|]+\|)\n((?:\|.+\|\n?)+)/gm, function (_, header, sep, body) {
            var ths = header.split("|").filter(Boolean).map(function (c) { return "<th>" + c.trim() + "</th>"; }).join("");
            var rows = body.trim().split("\n").map(function (row) {
                var tds = row.split("|").filter(Boolean).map(function (c) { return "<td>" + c.trim() + "</td>"; }).join("");
                return "<tr>" + tds + "</tr>";
            }).join("");
            return '<table><thead><tr>' + ths + '</tr></thead><tbody>' + rows + '</tbody></table>';
        });

        // Unordered list items
        html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
        html = html.replace(/((?:<li>.*<\/li>\s*)+)/g, "<ul>$1</ul>");

        // Ordered list items
        html = html.replace(/^\d+\.\s+(.+)$/gm, "<li>$1</li>");

        // Paragraphs
        html = html.replace(/^(?!<|$|\s*$)(.+)$/gm, "<p>$1</p>");

        return html;
    }

    function esc(s) {
        return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

})();
