from rest_framework import serializers

from hypha.apply.funds.models import RoundsAndLabs


class RoundLabSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoundsAndLabs
        fields = ("id", "title")


class OpenRoundLabSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    description = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()
    landing_url = serializers.SerializerMethodField()

    class Meta:
        model = RoundsAndLabs
        fields = (
            "id",
            "title",
            "url_path",
            "search_description",
            "start_date",
            "end_date",
            "description",
            "image",
            "weight",
            "landing_url",
        )

    def get_description(self, obj):
        if hasattr(obj, "roundbase"):
            return obj.roundbase.fund.applicationbase.description
        elif hasattr(obj, "labbase"):
            return obj.labbase.description
        return None

    def get_image(self, obj):
        if hasattr(obj, "roundbase"):
            fund_image = obj.roundbase.fund.applicationbase.image
            if fund_image:
                return fund_image.file.url
        elif hasattr(obj, "labbase"):
            lab_image = obj.labbase.image
            if lab_image:
                return lab_image.url
        return None

    def get_weight(self, obj):
        if hasattr(obj, "roundbase"):
            return obj.roundbase.fund.applicationbase.weight
        elif hasattr(obj, "labbase"):
            return obj.labbase.weight
        return None

    def get_landing_url(self, obj):
        if hasattr(obj, "roundbase"):
            return obj.roundbase.fund.applicationbase.get_full_url()
        elif hasattr(obj, "labbase"):
            return obj.labbase.get_full_url()
        return None
