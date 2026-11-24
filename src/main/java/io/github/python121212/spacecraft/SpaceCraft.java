package io.github.python121212.spacecraft;

import io.github.python121212.spacecraft.item.WrenchItem;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/**
 * 宇宙クラフト（Space Craft）のエントリポイント。
 *
 * <p>Forge は {@code @Mod} をスキャンしてこのクラスを読み込みます。modId は
 * META-INF/mods.toml の {@code spacecraft} と一致させてください。</p>
 */
@Mod(SpaceCraft.MOD_ID)
public class SpaceCraft {

    public static final String MOD_ID = "spacecraft";

    /** アイテムの登録先。 */
    public static final DeferredRegister<Item> ITEMS =
        DeferredRegister.create(ForgeRegistries.ITEMS, MOD_ID);

    /** クリエイティブタブの登録先。 */
    public static final DeferredRegister<CreativeModeTab> CREATIVE_TABS =
        DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MOD_ID);

    /** 最初のアイテム: ブロックを右クリックで 90 度回転させるレンチ。 */
    public static final RegistryObject<Item> WRENCH = ITEMS.register("wrench",
        () -> new WrenchItem(new Item.Properties().stacksTo(1)));

    /** 宇宙クラフト専用のクリエイティブタブ。 */
    public static final RegistryObject<CreativeModeTab> SPACE_CRAFT_TAB =
        CREATIVE_TABS.register("spacecraft", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.spacecraft"))
            .icon(() -> new ItemStack(WRENCH.get()))
            .displayItems((params, output) -> output.accept(WRENCH.get()))
            .build());

    public SpaceCraft() {
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        ITEMS.register(bus);
        CREATIVE_TABS.register(bus);
    }
}
