package com.example.buzzbraceletadmin;

import android.os.Environment;

import com.google.gson.*;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Date;
import java.util.ArrayList;
import java.text.SimpleDateFormat;

public class Blockchain extends HashableObject {
    public ArrayList<Block> blocks;
    public String timestamp;

    public Blockchain() {
        blocks = new ArrayList<Block>();
        timestamp = new SimpleDateFormat("yyy-MM-dd'T'HH:mm:ss").format(new Date());
    }

    public void genesis(ArrayList<Transaction> t) throws Exception {
        if (blocks.isEmpty()) {
            blocks.add(new Block("0", t));
        } else {
            throw new Exception("Can't re-initialise the blockchain");
        }
    }

    public void newBlock(Block b) {
        blocks.add(b);
        timestamp = new SimpleDateFormat("yyy-MM-dd'T'HH:mm:ss").format(new Date());
    }

    public void export() {
        File f = new File(Environment.getExternalStorageDirectory().getAbsolutePath() + "blockchain.json");
        try {
            f.createNewFile();
            FileWriter w = new FileWriter(f, false);
            w.write(this.toJson());
            w.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void rebuild(String j){
        Blockchain tmp = new Gson().fromJson(j, Blockchain.class);
        blocks = tmp.blocks;
        timestamp = tmp.timestamp;
    }

    public Block getLastBlock(){
        return blocks.get(blocks.size() - 1);
    }
}