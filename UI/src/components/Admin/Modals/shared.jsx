export const openDialog = (dialog) => {
    dialog.classList.remove('hidden', 'animate-exit')
    dialog.classList.add('animate-enter')
}

export const closeDialog = (dialog, timeout=300) => {
    dialog.classList.remove('animate-enter')
    dialog.classList.add('animate-exit')
    setTimeout(() => {
        dialog.classList.add('hidden')
    }, timeout)
}
