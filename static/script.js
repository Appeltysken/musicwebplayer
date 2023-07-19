$(document).ready(function () {
    $('.favorite-btn').click(function () {
        var trackId = $(this).data('track-id');
        var isFavorite = $(this).hasClass('favorite');
        var messageSpan = $(this).siblings('.message');

        $.ajax({
            url: '/musicwebplayer/toggle_favorite',
            type: 'POST',
            data: JSON.stringify({ trackId: trackId, isFavorite: isFavorite }),
            contentType: 'application/json',
            success: function (response) {
                if (response.success) {
                    var button = $('.favorite-btn[data-track-id="' + trackId + '"]');
                    button.toggleClass('favorite', response.is_favorite);

                    var icon = button.find('i');
                    if (response.is_favorite) {
                        icon.removeClass('far fa-star').addClass('fas fa-star');
                    } else {
                        icon.removeClass('fas fa-star').addClass('far fa-star');
                    }

                    if (response.is_favorite) {
                        showMessage(messageSpan, 'Трек добавлен в избранное');
                    } else {
                        showMessage(messageSpan, 'Трек удален из избранного');
                    }
                }
            }
        });
    });
});

function showMessage(element, message) {
    element.text(message);
    element.addClass('show');
    setTimeout(function () {
        element.removeClass('show');
    }, 2000);
}