/* --------------------------------------------------------------------------
 * CrowdFund Egypt - Client Interactivity & UI Controller
 * -------------------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss alerts after 5 seconds
    const alertList = document.querySelectorAll('.alert-dismissible');
    alertList.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 2. Toggle Comment Reply Form
    const replyButtons = document.querySelectorAll('.btn-reply-toggle');
    replyButtons.forEach(button => {
        button.addEventListener('click', function () {
            const commentId = this.getAttribute('data-comment-id');
            const targetForm = document.getElementById(`reply-form-${commentId}`);
            if (targetForm) {
                targetForm.classList.toggle('d-none');
            }
        });
    });

    // 3. Multi-image file input preview names
    const multiFileInput = document.querySelector('input[type="file"][multiple]');
    if (multiFileInput) {
        multiFileInput.addEventListener('change', function () {
            const previewContainer = document.getElementById('gallery-file-names');
            if (previewContainer) {
                previewContainer.innerHTML = '';
                const files = Array.from(this.files);
                if (files.length > 0) {
                    const list = document.createElement('ul');
                    list.className = 'list-inline small text-muted mt-2';
                    files.forEach(f => {
                        const item = document.createElement('li');
                        item.className = 'list-inline-item me-2 badge bg-light text-dark border';
                        item.textContent = f.name;
                        list.appendChild(item);
                    });
                    previewContainer.appendChild(list);
                }
            }
        });
    }

    // 4. Report Comment Modal helper
    const reportButtons = document.querySelectorAll('.btn-report-comment');
    const reportedCommentInput = document.getElementById('id_reported_comment_id');
    reportButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const commentId = this.getAttribute('data-comment-id');
            if (reportedCommentInput) {
                reportedCommentInput.value = commentId;
            }
        });
    });
});
