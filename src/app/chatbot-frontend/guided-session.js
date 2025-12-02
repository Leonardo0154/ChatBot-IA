document.addEventListener('DOMContentLoaded', () => {
    // Guided sessions are now created as assignments of type 'guided_session'.
    // Redirect teachers/parents to the assignment creation page with the type preselected.
    const params = new URLSearchParams(window.location.search);
    const pretype = params.get('type');
    if (pretype === 'guided_session') {
        window.location.href = 'create-assignment.html?type=guided_session';
    } else {
        // Default behavior: redirect to create assignment page where user can choose guided session
        window.location.href = 'create-assignment.html?type=guided_session';
    }
});
