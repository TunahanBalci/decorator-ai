package net.aproximo.decoratorai.model.entity;

import com.google.type.DateTime;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.Dictionary;
import java.util.UUID;


@Entity
@Table(uniqueConstraints =
    @UniqueConstraint(columnNames = "product_id")
)
public class ProductEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column
    @NotNull
    private String externalId;

    @Column
    @Size(min = 3, max = 256)
    private String source;

    @Column
    @Size(min = 8, max = 512)
    private String sourceUrl;

    @Column
    @Size(min = 3, max = 256)
    private String name;

    @Column
    @Size(min = 3, max = 2048)
    private String description;

    @Column
    @NotNull
    @NotBlank
    @Size(min = 3, max = 64)
    private String category;

    @Column
    @NotNull
    @NotBlank
    private float priceAmount;

    @Column
    @NotNull
    @NotBlank
    @Size(min = 1, max = 32)
    private String priceCurrency;

    @Column
    @NotNull
    @NotBlank
    private float widthCm;


    @Column
    @NotNull
    @NotBlank
    private float depthCm;


    @Column
    @NotNull
    @NotBlank
    private float heightCm;

    @Column
    private String[] materials;

    @Column
    private String[] colors;

    @Column
    private String[] styles;

    @Column
    private String temperature;

    @Column
    private String[] roomTypes;

    @NotNull
    private boolean isGroup;


    @Column
    private ProductEntity[] groupItems;


    @Column
    private Dictionary rawMetadata;
    @Column
    private Dictionary enrichedMetadata;
    @Column
    private Dictionary metadataConfidence;

    @Column
    private Dictionary semanticText;
    @Column
    private Dictionary shape;
    @Column
    private String[] visualFeatures;
    @Column
    private String[] designTags;
    @Column
    private String visualWeight;
    @Column
    private String spatialWeight;
    @Column
    private String[] usageIntent;
    @Column
    private String qualityTier;

    @Column
    private boolean isActive;
    @Column
    private DateTime createdAt;
    @Column
    private DateTime updatedAt;


    public UUID getId() {
        return id;
    }

    public String getExternalId() {
        return externalId;
    }

    public String getSource() {
        return source;
    }

    public String getSourceUrl() {
        return sourceUrl;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public String getCategory() {
        return category;
    }

    public float getPriceAmount() {
        return priceAmount;
    }

    public String getPriceCurrency() {
        return priceCurrency;
    }

    public float getWidthCm() {
        return widthCm;
    }

    public float getDepthCm() {
        return depthCm;
    }

    public float getHeightCm() {
        return heightCm;
    }

    public String[] getMaterials() {
        return materials;
    }

    public String[] getColors() {
        return colors;
    }

    public String[] getStyles() {
        return styles;
    }

    public String getTemperature() {
        return temperature;
    }

    public String[] getRoomTypes() {
        return roomTypes;
    }

    public boolean isGroup() {
        return isGroup;
    }

    public ProductEntity[] getGroupItems() {
        return groupItems;
    }

    public Dictionary getRawMetadata() {
        return rawMetadata;
    }

    public Dictionary getEnrichedMetadata() {
        return enrichedMetadata;
    }

    public Dictionary getMetadataConfidence() {
        return metadataConfidence;
    }

    public Dictionary getSemanticText() {
        return semanticText;
    }

    public Dictionary getShape() {
        return shape;
    }

    public String[] getVisualFeatures() {
        return visualFeatures;
    }

    public String[] getDesignTags() {
        return designTags;
    }

    public String getVisualWeight() {
        return visualWeight;
    }

    public String getSpatialWeight() {
        return spatialWeight;
    }

    public String[] getUsageIntent() {
        return usageIntent;
    }

    public String getQualityTier() {
        return qualityTier;
    }

    public boolean isActive() {
        return isActive;
    }

    public DateTime getCreatedAt() {
        return createdAt;
    }

    public DateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setActive(boolean active) {
        isActive = active;
    }

    public void setUpdatedAt(DateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}