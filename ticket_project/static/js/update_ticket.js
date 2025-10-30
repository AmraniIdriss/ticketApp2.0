"use strict";

// Wait for the DOM to be fully loaded before running the script
document.addEventListener("DOMContentLoaded", () => {
    console.log("JS loaded and DOM ready");

    // -------------------
    // UTILS
    // -------------------
    const $ = (sel, scope = document) => scope.querySelector(sel);
    const getCookie = (name) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return decodeURIComponent(parts.pop().split(";").shift());
        return null;
    };
    const getCSRF = () =>
        document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
        getCookie("csrftoken") ||
        "";

    // -------------------
    // MODAL + FORM ELEMENTS
    // -------------------
    const modalElement = document.getElementById("updateTicketModal");
    const modal = new bootstrap.Modal(modalElement);
    const form = document.getElementById("updateTicketForm");
    const dynamicFieldsContainer = document.getElementById("dynamicFieldsContainer");
    const modalTitle = document.getElementById("modalTicketId");

    // Template fields for each activity type (keys must match exactly, including symbols)
    const templateFields = {
        "♣ Development": ["observations", "development details", "details evidences"],
        "♦ Release Deployment": ["observations", "development details", "details evidences"],
        "Project": ["observations", "development details", "details evidences"],
        "Maintenance Activity": ["observations", "analysis resolution details", "recommendations", "details evidences"],
        "☛ Solicitation": ["observations", "resolution_details", "recommendations", "details evidences"],
        "⚠️ Incident": ["observations", "analysis", "root cause", "resolution details", "recommendations", "details evidences"],
        "☠ Trouble Ticket": ["error description", "resolution investigation details", "recommendations", "details evidences"]
    };

    // Normalization function: trims and normalizes spaces, preserves Unicode symbols
    const normalize = str => {
        if (!str) return "";
        return str.trim().replace(/\s+/g, " ");
    };

    // -------------------
    // EDIT BUTTON (Activity Resolution)
    // -------------------
    document.querySelectorAll(".btn-update-ticket").forEach(btn => {
        btn.addEventListener("click", () => {
            const ticketId = btn.dataset.ticketId;
            const row = btn.closest("tr");
            const activityTypeName = row.querySelector("td:nth-child(7)").textContent.trim();

            modalTitle.textContent = `Update Ticket #${ticketId}`;
            dynamicFieldsContainer.innerHTML = "";

            const matchedKey = Object.keys(templateFields)
                .find(k => normalize(k) === normalize(activityTypeName));

            const fields = templateFields[matchedKey] || [];

            console.log("Activity Type:", activityTypeName);
            console.log("Matched Key:", matchedKey);
            console.log("Fields:", fields);

            if (fields.length === 0) {
                dynamicFieldsContainer.innerHTML = `
                    <div class="alert alert-warning">
                        No fields defined for activity type: <strong>${activityTypeName}</strong>
                    </div>
                `;
            } else {
                fields.forEach(f => {
                    const formGroup = document.createElement("div");
                    formGroup.className = "mb-3";
                    const label = f.replace(/_/g, " ")
                        .split(" ")
                        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(" ");
                    formGroup.innerHTML = `
                        <label class="form-label fw-bold">${label}</label>
                        <textarea class="form-control" name="${f}" rows="3"></textarea>
                    `;
                    dynamicFieldsContainer.appendChild(formGroup);
                });
            }

            const hiddenInput = document.createElement("input");
            hiddenInput.type = "hidden";
            hiddenInput.name = "ticket_id";
            hiddenInput.value = ticketId;
            dynamicFieldsContainer.appendChild(hiddenInput);

            modal.show();
        });
    });

    // -------------------
    // FORM SUBMIT
    // -------------------
    form.addEventListener("submit", e => {
        e.preventDefault();
        const csrfToken = getCSRF();
        const formData = new FormData(form);
        const url = form.dataset.url;

        fetch(url, {
            method: "POST",
            headers: { 
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest"
            },
            body: formData
        })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (data.status === "success") {
                const ticketId = formData.get("ticket_id");
                const row = document.querySelector(`.btn-update-ticket[data-ticket-id='${ticketId}']`).closest("tr");
                const resolutionCell = row.querySelector("td:nth-child(15) span");

                const resolutionParts = Array.from(formData.entries())
                    .filter(([k]) => k !== "ticket_id" && k !== "csrfmiddlewaretoken")
                    .map(([k, v]) => {
                        if (v.trim()) {
                            const label = k.replace(/_/g, " ")
                                .split(" ")
                                .map(w => w.charAt(0).toUpperCase() + w.slice(1))
                                .join(" ");
                            return `${label}: ${v}`;
                        }
                        return null;
                    })
                    .filter(Boolean)
                    .join("; ");

                resolutionCell.textContent = resolutionParts || "No details";

                const alertDiv = document.createElement("div");
                alertDiv.className = "alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3";
                alertDiv.style.zIndex = "9999";
                alertDiv.innerHTML = `
                    ✓ Ticket #${ticketId} updated successfully
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.body.appendChild(alertDiv);
                setTimeout(() => alertDiv.remove(), 3000);

                modal.hide();
            } else {
                alert("❌ Error updating ticket: " + (data.error || "Unknown error"));
            }
        })
        .catch(err => {
            console.error("Fetch error:", err);
            alert("❌ Network error. Please try again.");
        });
    });


    // -------------------
    // TIMER STOP HANDLER (update status instantly)
    // -------------------
    document.querySelectorAll(".btn-stop").forEach(btnStop => {
        btnStop.addEventListener("click", () => {
            const ticketId = btnStop.dataset.ticketId;
            const csrfToken = getCSRF();
            const url = `/tickets/stop/${ticketId}/`; // <-- adapte ce endpoint à ton URL Django

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    console.log(`✅ Ticket #${ticketId} stopped`);

                    const row = document.querySelector(`.btn-stop[data-ticket-id='${ticketId}']`).closest("tr");
                    const statusBadge = row.querySelector(".status-badge");

                    if (statusBadge) {
                        statusBadge.textContent = "Finished";
                        statusBadge.classList.remove("bg-success", "bg-warning", "bg-primary");
                        statusBadge.classList.add("bg-secondary");
                    }

                    const alertDiv = document.createElement("div");
                    alertDiv.className = "alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3";
                    alertDiv.style.zIndex = "9999";
                    alertDiv.innerHTML = `
                        ✓ Ticket #${ticketId} stopped and marked as Finished
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    document.body.appendChild(alertDiv);
                    setTimeout(() => alertDiv.remove(), 3000);
                } else {
                    alert("❌ Error stopping ticket: " + (data.error || "Unknown error"));
                }
            })
            .catch(err => {
                console.error("Fetch error:", err);
                alert("❌ Network error while stopping ticket.");
            });
        });
    });
});
