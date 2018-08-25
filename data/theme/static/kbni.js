function set_link_elements_active() {
    var pathname = document.location.pathname.toString();
    jQuery('[href="'+document.location.pathname+'"]').addClass('active')
    jQuery('.nav-link').each(function(i, obj){
        var href = jQuery(obj).attr('href');
        if (pathname == href || (href !== '/' && pathname.startsWith(href)))
            jQuery(obj).addClass('active');
    });
}

$(document).ready(function () {
    set_link_elements_active();
});