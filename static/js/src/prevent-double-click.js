$('#operational').submit(function(){
    $this = $(this);
    console.log($this.data().isSubmitted)
    /** prevent double posting */
    if ($this.data().isSubmitted) {
        return false;
    }

    /** mark the form as processed, so we will not process it again */
    $this.data().isSubmitted = true;
    return true;
});
