window.dash_extensions = Object.assign({}, window.dash_extensions, {
    default: {
        function0: function(feature, latlng) {
            const {min, max, "text": text, "title": title} = feature.properties;
            const icon = L.divIcon({
                html: `<div style="text-align: center; font-size: 14px; font-weight: bold;">${text}</div>`,
                className: "marker-cluster",
                iconSize: [40, 40]
            });
            return L.marker(latlng, {icon: icon, title: title});
        }
    }
});
