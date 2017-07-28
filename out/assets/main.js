function checkVisa(){
    var ccode = $('#country-code').val();
    var nationality = $('#nat').val();
    var $result = $('#visaresult');
    if(nationality){
        $result.show().html('Loading visa status...');
        setTimeout(function(){
            $.getJSON('../data/' + nationality.toLowerCase() + '-' + ccode.toLowerCase() + '.json', function(data){
                $result.show().html('Visa status: <strong>' + data.visa + "</strong>");
            });
        }, 1000);
    }
    return false;
}

$('#check-btn').click(checkVisa);
$('form').submit(checkVisa);
var $more = $('#showMore').click(function(){
    $more.hide();
    $('table').show();
});

