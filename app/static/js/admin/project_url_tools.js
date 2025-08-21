// Copyright (C) 2010-2025 Université de Lausanne, RISET
// See docs/copyright.md
// JS pour boutons "générer" et "vérifier" le slug dans l'admin Project


// Copyright (C) 2010-2025 Université de Lausanne, RISET
// See docs/copyright.md


(function($){
    $(document).ready(function(){
        var $url = $("#id_url");
        var $name = $("#id_name");
        if (!$url.length || !$name.length) return;

        // Délégation d'événement pour robustesse
        $(document).on("click", ".generate-btn", function(e){
            e.preventDefault();
            if (typeof URLify === 'function') {
                $url.val(URLify($name.val(), 50));
            } else {
                alert("La fonction URLify n'est pas chargée.");
            }
        });

        $(document).on("click", ".check-btn", function(e){
            e.preventDefault();
            var val = $url.val();
            if (!val) {
                alert("Le slug ne peut pas être vide.");
                return;
            }
            // Vérification stricte : lettres, chiffres, tirets
            if (!/^[a-z0-9-]+$/.test(val)) {
                alert("Le slug ne doit contenir que des lettres minuscules, chiffres ou tirets.");
            } else {
                alert("Slug valide !");
            }
        });
    });
})(django.jQuery || window.jQuery);
