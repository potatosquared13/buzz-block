package com.example.buzzbraceletvendor;

import android.content.Context;
import android.os.Environment;

import com.google.gson.Gson;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;

public class Blockchain extends HashableObject {
    public ArrayList<Block> blocks;
    public ArrayList<Transaction> pending_transactions;
    public String timestamp;

    public Blockchain() {
        blocks = new ArrayList<Block>();
        pending_transactions = new ArrayList<Transaction>();
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

    public void export(Context c) {
        File f = new File(c.getExternalFilesDir(null), "blockchain.json");
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
        pending_transactions = tmp.pending_transactions;
    }

    public Block getLastBlock(){
        return blocks.get(blocks.size() - 1);
    }
}