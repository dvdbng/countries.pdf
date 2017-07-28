
$('button').click(function(){
    $('#loading').show();
    setTimeout(function(){
        $('#loading').hide();
        $('p').show();
    }, 1000);
    return false;
});

