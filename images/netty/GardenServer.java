/*
 * Copyright 2012 The Netty Project
 *
 * The Netty Project licenses this file to you under the Apache License,
 * version 2.0 (the "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at:
 *
 *   https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * Modified by Ben Kallus for the HTTP Garden.
 */

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.logging.LogLevel;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelPipeline;
import io.netty.channel.socket.SocketChannel;
import io.netty.handler.codec.http.HttpRequestDecoder;
import io.netty.handler.codec.http.HttpResponseEncoder;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.channel.ChannelFutureListener;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.handler.codec.http.DefaultFullHttpResponse;
import io.netty.handler.codec.http.FullHttpResponse;
import io.netty.handler.codec.http.HttpContent;
import io.netty.handler.codec.http.HttpHeaderNames;
import io.netty.handler.codec.http.HttpUtil;
import io.netty.handler.codec.http.HttpHeaderValues;
import io.netty.handler.codec.http.HttpHeaders;
import io.netty.handler.codec.http.HttpObject;
import io.netty.handler.codec.http.HttpRequest;
import io.netty.handler.codec.http.LastHttpContent;
import io.netty.util.CharsetUtil;

import java.util.Base64;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Map;
import java.util.Map.Entry;

import static io.netty.handler.codec.http.HttpResponseStatus.*;
import static io.netty.handler.codec.http.HttpVersion.*;

class GardenServerHandler extends SimpleChannelInboundHandler <Object> {
    private static String base64_encode(byte[] input) {
        return Base64.getEncoder().encodeToString(input);
    }

    private HttpRequest request;
    // Buffer that stores the response content
    private final StringBuilder buf = new StringBuilder();
    private final ByteArrayOutputStream body = new ByteArrayOutputStream();

    @Override
    public void channelReadComplete(ChannelHandlerContext ctx) {
        ctx.flush();
    }

    @Override
    protected void channelRead0(ChannelHandlerContext ctx, Object msg) throws IOException {
        if (msg instanceof HttpRequest) {
            HttpRequest request = this.request = (HttpRequest) msg;
            if (!request.decoderResult().isSuccess()) {
                throw new IOException();
            }

            buf.setLength(0);
            body.reset();

            buf.append("{\"version\":\"").append(base64_encode(request.protocolVersion().text().getBytes(CharsetUtil.ISO_8859_1))).append("\",");

            buf.append("\"method\":\"").append(base64_encode(request.getMethod().toString().getBytes(CharsetUtil.ISO_8859_1))).append("\",");

            buf.append("\"uri\":\"").append(base64_encode(request.uri().getBytes(CharsetUtil.ISO_8859_1))).append("\",");

            buf.append("\"headers\":[");
            HttpHeaders headers = request.headers();
            boolean first = true;
            for (Map.Entry < String, String > h: headers) {
                if (!first) {
                    buf.append(",");
                }
                buf.append("[\"").append(base64_encode(h.getKey().getBytes(CharsetUtil.ISO_8859_1))).append("\",\"").append(base64_encode(h.getValue().getBytes(CharsetUtil.ISO_8859_1))).append("\"]");
                first = false;
            }
            buf.append("],");
        }

        if (msg instanceof HttpContent) {
            HttpContent httpContent = (HttpContent) msg;
            if (!httpContent.decoderResult().isSuccess()) {
                throw new IOException();
            }

            ByteBuf content = httpContent.content();
            if (content.isReadable()) {
                body.write(content.toString(CharsetUtil.ISO_8859_1).getBytes(CharsetUtil.ISO_8859_1));
            }

            if (msg instanceof LastHttpContent) {
                LastHttpContent trailer = (LastHttpContent) msg;
                if (!trailer.decoderResult().isSuccess()) {
                    throw new IOException();
                }
                buf.append("\"body\":\"").append(base64_encode(body.toByteArray())).append("\"}");
                if (!writeResponse(trailer, ctx)) {
                    ctx.writeAndFlush(Unpooled.EMPTY_BUFFER).addListener(ChannelFutureListener.CLOSE);
                }
            }
        }
    }

    private boolean writeResponse(HttpObject currentObj, ChannelHandlerContext ctx) {
        // Decide whether to close the connection or not.
        boolean keepAlive = HttpUtil.isKeepAlive(request);
        // Build the response object.
        FullHttpResponse response = new DefaultFullHttpResponse(
            HTTP_1_1, currentObj.decoderResult().isSuccess() ? OK : BAD_REQUEST,
            Unpooled.copiedBuffer(buf.toString(), CharsetUtil.ISO_8859_1));

        response.headers().setInt(HttpHeaderNames.CONTENT_LENGTH, response.content().readableBytes());
        if (keepAlive) {
            response.headers().set(HttpHeaderNames.CONNECTION, HttpHeaderValues.KEEP_ALIVE);
        }

        // Write the response.
        ctx.write(response);

        return keepAlive;
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        cause.printStackTrace();
        ctx.close();
    }
}

class GardenServerInitializer extends ChannelInitializer < SocketChannel > {

    @Override
    public void initChannel(SocketChannel ch) {
        ChannelPipeline p = ch.pipeline();
        p.addLast(new HttpRequestDecoder());
        p.addLast(new HttpResponseEncoder());
        p.addLast(new GardenServerHandler());
    }
}

public final class GardenServer {

    public static void main(String[] args) throws Exception {
        // Configure the server.
        EventLoopGroup bossGroup = new NioEventLoopGroup(1);
        EventLoopGroup workerGroup = new NioEventLoopGroup();
        try {
            ServerBootstrap b = new ServerBootstrap();
            b.group(bossGroup, workerGroup)
                .channel(NioServerSocketChannel.class)
                .childHandler(new GardenServerInitializer());

            Channel ch = b.bind(80).sync().channel();

            ch.closeFuture().sync();
        } finally {
            bossGroup.shutdownGracefully();
            workerGroup.shutdownGracefully();
        }
    }
}
