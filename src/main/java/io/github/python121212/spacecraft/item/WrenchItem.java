package io.github.python121212.spacecraft.item;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 宇宙クラフトのレンチ。
 *
 * <p>ブロックに右クリックすると、そのブロックステートを時計回りに 90 度回転させます
 * （向きを持たないブロックには何もしません）。耐久値は無く、1 個までしかスタックしません。</p>
 */
public class WrenchItem extends Item {

    public WrenchItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Level level = context.getLevel();
        BlockPos pos = context.getClickedPos();
        BlockState state = level.getBlockState(pos);
        BlockState rotated = state.rotate(level, pos, Rotation.CLOCKWISE_90);

        // 向きを持たないブロックなど、回転で状態が変わらない場合は何もしない
        if (rotated == state) {
            return InteractionResult.PASS;
        }

        if (!level.isClientSide) {
            level.setBlock(pos, rotated, Block.UPDATE_ALL);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }
}
