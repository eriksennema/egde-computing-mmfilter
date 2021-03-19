package main

import java.awt.image.BufferedImage
import java.io.{BufferedReader, InputStreamReader, PrintStream, PrintWriter}
import java.net.{ServerSocket, Socket}
import java.nio.charset.StandardCharsets
import java.util

import collection.JavaConversions._
import scala.io.BufferedSource
import scala.util.control._
import scala.io._
import scala.util._
import net.{GatedEmbeddingUnit, TemporalAggregation}
import org.datavec.image.loader.{ImageLoader, Java2DNativeImageLoader}
import org.nd4j.linalg.api.ndarray.INDArray
import org.nd4j.linalg.factory.Nd4j

import scala.collection.immutable.Stack

object Main extends App {

//  val s1 = Stack(5, 3, 2, 7, 6, 1)
//
//  // Print the stack
//  println(s1)
//
//  // Applying top method
//  val result = s1.top
//
//  // Display output
//  print("Top element of the stack: " + result, s1)

  val dim1 = 256
  val window_size = 12

  // socket server part
  val loop = new Breaks
  val inner_loop = new Breaks
  var msg = new String
  val FRAME_RECEIVE_PORT = 10002
  val listener: ServerSocket = new ServerSocket(FRAME_RECEIVE_PORT)

  println("Socket server is starting...")
  loop.breakable{
    while (true) {
      // create socket
      val socket: Socket = listener.accept()
      var arrays: Array[INDArray] = Array()
      val in = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8))
      val out = new PrintWriter(socket.getOutputStream(), true)
      var input_line: String = in.readLine()
      var query_flag: Boolean = true
      var query_feature: INDArray = null
      var count: Int = 0
      inner_loop.breakable{
        while (input_line != null) {
          count += 1
          if (query_flag) {
            val query_feature_array: Array[Double] = input_line.split(",").map(_.toDouble)
            query_feature = Nd4j.create(query_feature_array).reshape(Array(1, dim1))
            // println(query_feature.shapeInfoToString())
            query_flag = false
          } else {
            val frames_array: Array[Double] = input_line.split(",").map(_.toDouble)
            val frames = Nd4j.create(frames_array).reshape(Array(1, dim1))
            arrays :+= frames
            // println(frames.shapeInfoToString())
          }
          if (count == window_size+1) {
            println("Has received 12 frames...")
            val array_collection: java.util.Collection[INDArray] = arrays.toSeq
            var frames = Nd4j.pile(array_collection)
            // println("res: ", frames.shapeInfoToString(), ", \n", query_feature.shapeInfoToString())

            // pooling layer
            val averagePool = new TemporalAggregation
            val temporal_agg = averagePool.run(frames)

            // GEU
            val geu = new GatedEmbeddingUnit
            val embedding1 = geu.run(temporal_agg)
            val embedding2 = geu.run(query_feature)

            val cos_dis = embedding1.mmul(embedding2.reshape(-1)).div(embedding1.norm2().mul(embedding2.norm2()))
            println("cosine dis: ", cos_dis)

            out.println(cos_dis)

            in.close()
            out.close()
            socket.close()
            inner_loop.break()
          }
          input_line = in.readLine()
        }
      }
    }
  }

//  // test
//  var frames = Nd4j.rand(12, 1*256) // data type: INDArray
//  frames = Nd4j.expandDims(frames, 1)
//  val averagePool = new TemporalAggregation
//  val temporal_agg = averagePool.run(frames)
//  println("output: ", temporal_agg.shapeInfoToString())
//
//  val query_embedding = Nd4j.rand(1, 256)
//  println("query: ", query_embedding.shapeInfoToString())
//
//  // test of GEU
//  val geu = new GatedEmbeddingUnit
//  val embedding1 = geu.run(temporal_agg)
//  val embedding2 = geu.run(query_embedding)
//
//  val cos_dis = embedding1.mmul(embedding2.reshape(-1)).div(embedding1.norm2().mul(embedding2.norm2()))
//  println("cosine dis: ", cos_dis)

//  var frames_str: String = _
//  var query_str: String = _
//  if (args.length < 2){
//    println("ERROR! NEED INPUT!")
//    System.exit(0)
//  } else {
//    frames_str = args(0)  // expect format: 1*12*1280*8*8
////    println("frames: ", frames_str)
//    query_str = args(1)  // expect format: 1280
////    println("query: ", query_str)
//  }

}